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

# 장비 카탈로그 (크기 정보) - 카탈로그에서 자동 import, 실패 시 fallback
try:
    from src.kitchen_simulator.data.equipment_catalog import EQUIPMENT_CATALOG
    EQUIPMENT_SIZES = {
        eq_id: (eq.width, eq.depth)
        for eq_id, eq in EQUIPMENT_CATALOG.items()
    }
except ImportError:
    # fallback: 카탈로그 import 실패 시 하드코딩
    EQUIPMENT_SIZES = {
        # 선반류
        "wall_shelf": (1.19, 0.35),
        "overhead_shelf": (1.31, 0.37),
        "multi_tier_shelf": (1.17, 0.60),
        "back_shelf": (1.24, 0.35),
        # 냉장류
        "table_refrigerator": (1.37, 0.70),
        "batt_table_refrigerator": (1.23, 0.68),
        "table_freezer": (1.20, 0.70),
        "box45_refrigerator_freezer": (1.26, 0.80),
        "box45_refrigerator": (1.26, 0.80),
        "beverage_showcase": (0.65, 0.61),
        "broth_refrigerator": (0.68, 0.51),
        "ice_maker": (0.59, 0.61),
        "reach_in_refrigerator_2door": (1.32, 0.76),
        "reach_in_refrigerator_1door": (0.66, 0.76),
        "reach_in_freezer_1door": (0.66, 0.76),
        "dry_storage_shelf": (1.2, 0.45),
        "undercounter_refrigerator": (0.7, 0.61),
        # 작업대
        "work_table_small": (0.9, 0.6),
        "work_table_medium": (1.01, 0.65),
        "prep_sink": (0.6, 0.55),
        "food_processor_station": (0.6, 0.5),
        # 조리
        "gas_range_3burner": (1.24, 0.61),
        "gas_range_4burner": (0.6, 0.7),
        "deep_fryer_single": (0.4, 0.76),
        "deep_fryer_double": (0.8, 0.76),
        "convection_oven": (0.9, 0.76),
        "griddle": (0.9, 0.6),
        "salamander": (0.6, 0.5),
        # 세척
        "one_comp_sink": (0.76, 0.64),
        "dishwasher_pre_sink": (1.17, 0.70),
        "dish_drying_rack": (0.77, 0.70),
        "scrap_table": (0.68, 0.69),
        "two_comp_sink": (1.40, 0.68),
        "dishwasher_undercounter": (0.89, 0.68),
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
    """단일 레이아웃 그리기 (번호 표기)"""

    # 전체 주방 경계 계산
    all_x = []
    all_y = []
    for zone in data.get("zones", []):
        for x, y in zone["polygon"]:
            all_x.append(x)
            all_y.append(y)

    if not all_x:
        return []

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
                color=ZONE_EDGE_COLORS.get(zone_type, "#333333"), alpha=0.5)

    # 2. 장비를 구역 순서대로 정렬 후 번호 부여
    zone_order = ["storage", "preparation", "cooking", "washing"]
    placements = data.get("placements", [])
    sorted_placements = sorted(placements, key=lambda p: (
        zone_order.index(p.get("zone", "")) if p.get("zone", "") in zone_order else 99,
        p.get("x", 0), p.get("y", 0)
    ))

    equipment_list = []
    for idx, placement in enumerate(sorted_placements, 1):
        x = placement["x"]
        y = placement["y"]
        rotation = placement.get("rotation", 0)
        equip_name = placement.get("equipment_name", placement["equipment_id"])
        zone_type = placement.get("zone", "")

        # 장비 크기
        w, h = get_equipment_size(placement["equipment_id"])
        if rotation == 90 or rotation == 270:
            w, h = h, w

        # 구역 색상으로 장비 채우기
        zone_color = ZONE_EDGE_COLORS.get(zone_type, "#666666")

        # 장비 사각형
        rect = Rectangle((x, y), w, h,
                         linewidth=1.5,
                         edgecolor=zone_color,
                         facecolor='white',
                         linestyle='-',
                         zorder=3)
        ax.add_patch(rect)

        # 번호 표기 (장비 중앙)
        fontsize = 7 if min(w, h) >= 0.5 else 5.5
        ax.text(x + w/2, y + h/2, str(idx),
                ha='center', va='center', fontsize=fontsize,
                color=zone_color, fontweight='bold', zorder=4)

        # 리스트용 데이터 수집
        equipment_list.append({
            "num": idx,
            "name": equip_name,
            "zone": ZONE_NAMES.get(zone_type, zone_type),
            "size": f"{placement.get('width', w)*1000:.0f}×{placement.get('depth', h)*1000:.0f}",
            "zone_type": zone_type,
        })

    # 3. 그리드 및 축
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.set_xlabel('X (m)', fontsize=8)
    ax.set_ylabel('Y (m)', fontsize=8)

    # 제목
    if title:
        ax.set_title(title, fontsize=11, fontweight='bold', pad=10)

    return equipment_list


def _draw_equipment_table(equipment_list, title_text, output_path):
    """설비 목록 테이블을 별도 이미지로 저장"""
    if not equipment_list:
        return

    # 구역별로 그룹핑
    zone_order = ["storage", "preparation", "cooking", "washing"]
    grouped = {}
    for eq in equipment_list:
        zt = eq["zone_type"]
        if zt not in grouped:
            grouped[zt] = []
        grouped[zt].append(eq)

    # 테이블 데이터 구성
    col_labels = ["No.", "설비명", "구역", "크기(mm)"]
    table_data = []
    cell_colors = []

    for zt in zone_order:
        if zt not in grouped:
            continue
        zone_color = ZONE_COLORS.get(zt, "#FFFFFF")
        for eq in grouped[zt]:
            table_data.append([
                str(eq["num"]),
                eq["name"],
                eq["zone"],
                eq["size"],
            ])
            cell_colors.append([zone_color] * 4)

    n_rows = len(table_data)
    fig_height = max(3, 1.0 + n_rows * 0.35)
    fig, ax = plt.subplots(figsize=(8, fig_height))
    ax.axis('off')
    ax.set_title(title_text, fontsize=11, fontweight='bold', pad=12)

    table = ax.table(
        cellText=table_data,
        colLabels=col_labels,
        cellColours=cell_colors,
        colColours=["#E0E0E0"] * 4,
        cellLoc='center',
        loc='center',
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.0, 1.4)

    # 헤더 스타일
    for j in range(len(col_labels)):
        table[0, j].set_text_props(fontweight='bold', fontsize=9)

    # 열 너비 조정
    col_widths = [0.08, 0.38, 0.14, 0.20]
    for j, w in enumerate(col_widths):
        for i in range(n_rows + 1):
            table[i, j].set_width(w)

    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"저장됨: {output_path}")
    plt.close()


def visualize_single(json_path, output_path=None):
    """단일 시뮬레이션 시각화 (도면 + 설비 리스트 별도 파일)"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 점수 정보
    scores = data.get("scores", {})
    overall = scores.get("overall", 0)
    input_info = data.get("input_summary", {})
    r_type = input_info.get("restaurant_type", "")
    seats = input_info.get("seat_count", 0)
    area = data.get("total_area_sqm", 0)

    # --- 도면 (별도 파일) ---
    fig, ax_layout = plt.subplots(figsize=(12, 9))
    title = f"주방 레이아웃 도면  |  {r_type} {seats}석  |  {area:.0f}㎡  |  종합 {overall:.0f}점"
    equipment_list = draw_layout(data, ax_layout, title=title)

    # 점수 바
    score_text = (
        f"동선 {scores.get('workflow_efficiency', 0)*100:.0f}%  |  "
        f"공간 {scores.get('space_utilization', 0)*100:.0f}%  |  "
        f"안전 {scores.get('safety_compliance', 0)*100:.0f}%  |  "
        f"접근 {scores.get('accessibility', 0)*100:.0f}%"
    )
    ax_layout.text(0.5, -0.06, score_text,
                   ha='center', va='top', fontsize=8, color='#666666',
                   transform=ax_layout.transAxes)

    layout_path = output_path or "layout.png"
    plt.savefig(layout_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"저장됨: {layout_path}")
    plt.close()

    # --- 설비 목록 (별도 파일) ---
    base = Path(layout_path)
    list_path = str(base.with_name(base.stem + "_list" + base.suffix))
    list_title = f"설비 목록  |  {r_type} {seats}석  |  총 {len(equipment_list)}종"
    _draw_equipment_table(equipment_list, list_title, list_path)


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
