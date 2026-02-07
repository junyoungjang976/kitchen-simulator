"""장비 카탈로그 - 한국 CAD DB 기반 표준 장비 규격 (396건, 1,416종 분석)"""
from typing import Dict, List
from ..domain.equipment import EquipmentSpec, EquipmentCategory

# ═══════════════════════════════════════════════════════════════
# 저장 구역 장비 (17종: 선반 4 + 냉장 8 + 기존 5)
# ═══════════════════════════════════════════════════════════════
STORAGE_EQUIPMENT: List[EquipmentSpec] = [
    # ── 선반류 (CAD 신규 4종) ──
    EquipmentSpec(
        id="wall_shelf",
        name="Wall Shelf",
        name_ko="벽선반",
        category=EquipmentCategory.STORAGE,
        width=1.19, depth=0.35, height=0.56,
        clearance_front=0.3,
        requires_wall=True,
        workflow_order=1,
    ),
    EquipmentSpec(
        id="overhead_shelf",
        name="Overhead Shelf",
        name_ko="상부선반",
        category=EquipmentCategory.STORAGE,
        width=1.31, depth=0.37, height=0.77,
        clearance_front=0.3,
        requires_wall=True,
        workflow_order=1,
    ),
    EquipmentSpec(
        id="multi_tier_shelf",
        name="Multi-tier Shelf",
        name_ko="다단식선반",
        category=EquipmentCategory.STORAGE,
        width=1.17, depth=0.60, height=1.78,
        clearance_front=0.6,
        requires_wall=True,
        workflow_order=1,
    ),
    EquipmentSpec(
        id="back_shelf",
        name="Back Shelf",
        name_ko="백선반",
        category=EquipmentCategory.STORAGE,
        width=1.24, depth=0.35, height=0.56,
        clearance_front=0.3,
        requires_wall=True,
        workflow_order=1,
    ),
    # ── 냉장류 (CAD 신규 8종) ──
    EquipmentSpec(
        id="table_refrigerator",
        name="Table Refrigerator",
        name_ko="테이블냉장고",
        category=EquipmentCategory.STORAGE,
        width=1.37, depth=0.70, height=0.85,
        clearance_front=0.6,
        workflow_order=2,
    ),
    EquipmentSpec(
        id="batt_table_refrigerator",
        name="Batt Table Refrigerator",
        name_ko="밧드테이블냉장고",
        category=EquipmentCategory.STORAGE,
        width=1.23, depth=0.68, height=0.85,
        clearance_front=0.6,
        workflow_order=2,
    ),
    EquipmentSpec(
        id="table_freezer",
        name="Table Freezer",
        name_ko="테이블냉동고",
        category=EquipmentCategory.STORAGE,
        width=1.20, depth=0.70, height=0.85,
        clearance_front=0.6,
        workflow_order=2,
    ),
    EquipmentSpec(
        id="box45_refrigerator_freezer",
        name="45-Box Refrigerator-Freezer",
        name_ko="45BOX냉동냉장고",
        category=EquipmentCategory.STORAGE,
        width=1.26, depth=0.80, height=1.89,
        clearance_front=0.9,
        requires_wall=True,
        workflow_order=3,
    ),
    EquipmentSpec(
        id="box45_refrigerator",
        name="45-Box Refrigerator",
        name_ko="45BOX올냉장고",
        category=EquipmentCategory.STORAGE,
        width=1.26, depth=0.80, height=1.90,
        clearance_front=0.9,
        requires_wall=True,
        workflow_order=3,
    ),
    EquipmentSpec(
        id="beverage_showcase",
        name="Beverage Showcase",
        name_ko="음료쇼케이스",
        category=EquipmentCategory.STORAGE,
        width=0.65, depth=0.61, height=1.84,
        clearance_front=0.6,
        requires_wall=True,
        workflow_order=4,
    ),
    EquipmentSpec(
        id="broth_refrigerator",
        name="Broth Refrigerator",
        name_ko="육수냉장고",
        category=EquipmentCategory.STORAGE,
        width=0.68, depth=0.51, height=0.93,
        clearance_front=0.6,
        workflow_order=4,
    ),
    EquipmentSpec(
        id="ice_maker",
        name="Ice Maker",
        name_ko="제빙기",
        category=EquipmentCategory.STORAGE,
        width=0.59, depth=0.61, height=0.96,
        clearance_front=0.6,
        requires_water=True,
        requires_drain=True,
        workflow_order=4,
    ),
    # ── 기존 유지 (크기 보정 포함) ──
    EquipmentSpec(
        id="reach_in_refrigerator_1door",
        name="Reach-in Refrigerator (1-door)",
        name_ko="업소용 냉장고 1도어",
        category=EquipmentCategory.STORAGE,
        width=0.66, depth=0.76, height=2.0,
        clearance_front=0.9,
        requires_wall=True,
        workflow_order=3,
    ),
    EquipmentSpec(
        id="reach_in_refrigerator_2door",
        name="Reach-in Refrigerator (2-door)",
        name_ko="업소용 냉장고 2도어",
        category=EquipmentCategory.STORAGE,
        width=1.32, depth=0.76, height=2.0,
        clearance_front=0.9,
        requires_wall=True,
        workflow_order=3,
    ),
    EquipmentSpec(
        id="reach_in_freezer_1door",
        name="Reach-in Freezer (1-door)",
        name_ko="업소용 냉동고 1도어",
        category=EquipmentCategory.STORAGE,
        width=0.66, depth=0.76, height=2.0,
        clearance_front=0.9,
        requires_wall=True,
        workflow_order=3,
    ),
    EquipmentSpec(
        id="dry_storage_shelf",
        name="Dry Storage Shelf",
        name_ko="건조 저장 선반",
        category=EquipmentCategory.STORAGE,
        width=1.2, depth=0.45, height=1.8,
        clearance_front=0.6,
        requires_wall=True,
        workflow_order=1,
    ),
    EquipmentSpec(
        id="undercounter_refrigerator",
        name="Undercounter Refrigerator",
        name_ko="언더카운터 냉장고",
        category=EquipmentCategory.STORAGE,
        width=0.7, depth=0.61, height=0.86,
        clearance_front=0.6,
        workflow_order=2,
    ),
]

# ═══════════════════════════════════════════════════════════════
# 전처리/준비 구역 장비 (4종 - work_table_large 제거, 통합)
# ═══════════════════════════════════════════════════════════════
PREPARATION_EQUIPMENT: List[EquipmentSpec] = [
    EquipmentSpec(
        id="work_table_small",
        name="Work Table (small)",
        name_ko="작업대 소형",
        category=EquipmentCategory.PREPARATION,
        width=0.9, depth=0.6, height=0.86,
        clearance_front=0.9,
        workflow_order=1,
    ),
    EquipmentSpec(
        id="work_table_medium",
        name="Work Table",
        name_ko="작업대",
        category=EquipmentCategory.PREPARATION,
        width=1.01, depth=0.65, height=0.86,  # CAD 평균
        clearance_front=0.9,
        workflow_order=1,
    ),
    EquipmentSpec(
        id="prep_sink",
        name="Prep Sink",
        name_ko="전처리 싱크대",
        category=EquipmentCategory.PREPARATION,
        width=0.6, depth=0.55, height=0.86,
        clearance_front=0.9,
        requires_water=True,
        requires_drain=True,
        workflow_order=2,
    ),
    EquipmentSpec(
        id="food_processor_station",
        name="Food Processor Station",
        name_ko="식품 가공기 스테이션",
        category=EquipmentCategory.PREPARATION,
        width=0.6, depth=0.5, height=0.86,
        clearance_front=0.6,
        workflow_order=3,
    ),
]

# ═══════════════════════════════════════════════════════════════
# 조리 구역 장비 (7종 - gas_range_6burner → gas_range_3burner)
# ═══════════════════════════════════════════════════════════════
COOKING_EQUIPMENT: List[EquipmentSpec] = [
    EquipmentSpec(
        id="gas_range_3burner",
        name="Gas Range (3-burner)",
        name_ko="가스3구렌지",
        category=EquipmentCategory.COOKING,
        width=1.24, depth=0.61, height=0.91,  # CAD 평균
        clearance_front=0.91, clearance_sides=0.46,
        requires_ventilation=True,
        workflow_order=2,
    ),
    EquipmentSpec(
        id="gas_range_4burner",
        name="Gas Range (4-burner)",
        name_ko="가스레인지 4구",
        category=EquipmentCategory.COOKING,
        width=0.6, depth=0.7, height=0.91,
        clearance_front=0.91, clearance_sides=0.46,
        requires_ventilation=True,
        workflow_order=2,
    ),
    EquipmentSpec(
        id="deep_fryer_single",
        name="Deep Fryer (single)",
        name_ko="튀김기 단일",
        category=EquipmentCategory.COOKING,
        width=0.4, depth=0.76, height=1.1,
        clearance_front=0.91,
        requires_ventilation=True,
        workflow_order=3,
    ),
    EquipmentSpec(
        id="deep_fryer_double",
        name="Deep Fryer (double)",
        name_ko="튀김기 더블",
        category=EquipmentCategory.COOKING,
        width=0.8, depth=0.76, height=1.1,
        clearance_front=0.91,
        requires_ventilation=True,
        workflow_order=3,
    ),
    EquipmentSpec(
        id="convection_oven",
        name="Convection Oven",
        name_ko="컨벡션 오븐",
        category=EquipmentCategory.COOKING,
        width=0.9, depth=0.76, height=1.5,
        clearance_front=1.2,
        requires_ventilation=True,
        workflow_order=4,
    ),
    EquipmentSpec(
        id="griddle",
        name="Griddle",
        name_ko="그리들",
        category=EquipmentCategory.COOKING,
        width=0.9, depth=0.6, height=0.91,
        clearance_front=0.91,
        requires_ventilation=True,
        workflow_order=1,
    ),
    EquipmentSpec(
        id="salamander",
        name="Salamander",
        name_ko="샐러맨더",
        category=EquipmentCategory.COOKING,
        width=0.6, depth=0.5, height=0.5,
        clearance_front=0.6,
        requires_ventilation=True,
        requires_wall=True,
        workflow_order=5,
    ),
]

# ═══════════════════════════════════════════════════════════════
# 세척 구역 장비 (9종: 신규 4종 + 기존 5종, 크기 보정)
# ═══════════════════════════════════════════════════════════════
WASHING_EQUIPMENT: List[EquipmentSpec] = [
    # ── 신규 세정대류 (CAD 4종) ──
    EquipmentSpec(
        id="one_comp_sink",
        name="1-Compartment Sink",
        name_ko="1조세정대",
        category=EquipmentCategory.WASHING,
        width=0.76, depth=0.64, height=0.85,
        clearance_front=0.9,
        requires_water=True,
        requires_drain=True,
        workflow_order=2,
    ),
    EquipmentSpec(
        id="dishwasher_pre_sink",
        name="Dishwasher Pre-rinse Sink",
        name_ko="1조세척기세정대",
        category=EquipmentCategory.WASHING,
        width=1.17, depth=0.70, height=0.85,
        clearance_front=0.9,
        requires_water=True,
        requires_drain=True,
        workflow_order=2,
    ),
    EquipmentSpec(
        id="dish_drying_rack",
        name="Dish Drying Rack",
        name_ko="식기건조대",
        category=EquipmentCategory.WASHING,
        width=0.77, depth=0.70, height=0.85,
        clearance_front=0.6,
        workflow_order=4,
    ),
    EquipmentSpec(
        id="scrap_table",
        name="Scrap Table",
        name_ko="잔반처리대",
        category=EquipmentCategory.WASHING,
        width=0.68, depth=0.69, height=0.85,
        clearance_front=0.6,
        workflow_order=1,
    ),
    # ── 기존 (크기 보정) ──
    EquipmentSpec(
        id="two_comp_sink",
        name="2-Compartment Sink",
        name_ko="2조세정대",
        category=EquipmentCategory.WASHING,
        width=1.40, depth=0.68, height=1.1,  # CAD 평균 (기존 three_compartment_sink 대체)
        clearance_front=0.9,
        requires_water=True,
        requires_drain=True,
        workflow_order=2,
    ),
    EquipmentSpec(
        id="dishwasher_undercounter",
        name="Undercounter Dishwasher",
        name_ko="식기세척기",
        category=EquipmentCategory.WASHING,
        width=0.89, depth=0.68, height=0.86,  # CAD 평균 (도어형)
        clearance_front=0.9,
        requires_water=True,
        requires_drain=True,
        workflow_order=3,
    ),
    EquipmentSpec(
        id="dishwasher_door_type",
        name="Door-type Dishwasher",
        name_ko="도어형 식기세척기",
        category=EquipmentCategory.WASHING,
        width=0.65, depth=0.75, height=1.5,
        clearance_front=1.2,
        requires_water=True,
        requires_drain=True,
        workflow_order=3,
    ),
    EquipmentSpec(
        id="drying_rack",
        name="Drying Rack",
        name_ko="건조대",
        category=EquipmentCategory.WASHING,
        width=1.0, depth=0.5, height=1.7,
        clearance_front=0.6,
        requires_wall=True,
        workflow_order=4,
    ),
    EquipmentSpec(
        id="hand_wash_sink",
        name="Hand Wash Sink",
        name_ko="손세정대",
        category=EquipmentCategory.WASHING,
        width=0.4, depth=0.35, height=0.86,
        clearance_front=0.6,
        requires_water=True,
        requires_drain=True,
        requires_wall=True,
        workflow_order=5,
    ),
]

# 전체 카탈로그
EQUIPMENT_CATALOG: Dict[str, EquipmentSpec] = {
    eq.id: eq
    for eq_list in [STORAGE_EQUIPMENT, PREPARATION_EQUIPMENT,
                    COOKING_EQUIPMENT, WASHING_EQUIPMENT]
    for eq in eq_list
}

# ═══════════════════════════════════════════════════════════════
# 식당 유형별 기본 장비 세트 (CAD top_10_by_business_type 기반)
# ═══════════════════════════════════════════════════════════════
DEFAULT_EQUIPMENT_SETS = {
    "korean": [
        # CAD 한식 상위 18종
        "work_table_medium",        # 2단작업대 → 작업대
        "wall_shelf",               # 벽선반
        "overhead_shelf",           # 상부선반
        "one_comp_sink",            # 1조세정대
        "table_refrigerator",       # 테이블냉장고
        "multi_tier_shelf",         # 다단식선반
        "dishwasher_undercounter",  # 식기세척기
        "back_shelf",               # 백선반
        "batt_table_refrigerator",  # 밧드테이블냉장고
        "work_table_medium",        # 작업대 (2번째)
        "gas_range_3burner",        # 가스3구렌지
        "box45_refrigerator_freezer",  # 45BOX냉동냉장고
        "broth_refrigerator",       # 육수냉장고
        "dish_drying_rack",         # 식기건조대
        "two_comp_sink",            # 2조세정대
        "scrap_table",              # 잔반처리대
        "hand_wash_sink",           # 손세정대
        "box45_refrigerator",       # 45BOX올냉장고
    ],
    "chinese": [
        "work_table_medium",
        "wall_shelf",
        "overhead_shelf",
        "one_comp_sink",
        "table_refrigerator",
        "gas_range_3burner",
        "gas_range_4burner",
        "deep_fryer_double",
        "multi_tier_shelf",
        "dishwasher_undercounter",
        "box45_refrigerator_freezer",
        "hand_wash_sink",
        "back_shelf",
        "two_comp_sink",
    ],
    "japanese": [
        "work_table_medium",
        "wall_shelf",
        "overhead_shelf",
        "one_comp_sink",
        "table_refrigerator",
        "reach_in_refrigerator_1door",
        "reach_in_freezer_1door",
        "multi_tier_shelf",
        "gas_range_4burner",
        "deep_fryer_single",
        "dishwasher_undercounter",
        "hand_wash_sink",
        "back_shelf",
        "two_comp_sink",
    ],
    "western": [
        "work_table_medium",
        "wall_shelf",
        "overhead_shelf",
        "one_comp_sink",
        "table_refrigerator",
        "gas_range_3burner",
        "convection_oven",
        "deep_fryer_single",
        "griddle",
        "multi_tier_shelf",
        "dishwasher_undercounter",
        "hand_wash_sink",
        "back_shelf",
        "two_comp_sink",
        "box45_refrigerator_freezer",
    ],
    "cafe": [
        "work_table_medium",
        "wall_shelf",
        "overhead_shelf",
        "one_comp_sink",
        "table_refrigerator",
        "beverage_showcase",
        "ice_maker",
        "undercounter_refrigerator",
        "multi_tier_shelf",
        "hand_wash_sink",
        "two_comp_sink",
    ],
    "fast_food": [
        "work_table_medium",
        "wall_shelf",
        "table_refrigerator",
        "gas_range_4burner",
        "deep_fryer_double",
        "griddle",
        "one_comp_sink",
        "hand_wash_sink",
        "multi_tier_shelf",
        "box45_refrigerator_freezer",
        "overhead_shelf",
    ],
    "casual": [
        "work_table_medium",
        "wall_shelf",
        "overhead_shelf",
        "one_comp_sink",
        "table_refrigerator",
        "gas_range_3burner",
        "deep_fryer_single",
        "convection_oven",
        "multi_tier_shelf",
        "dishwasher_undercounter",
        "hand_wash_sink",
        "back_shelf",
        "two_comp_sink",
        "box45_refrigerator_freezer",
    ],
    "fine_dining": [
        "work_table_medium",
        "work_table_medium",
        "wall_shelf",
        "overhead_shelf",
        "one_comp_sink",
        "table_refrigerator",
        "reach_in_refrigerator_2door",
        "reach_in_freezer_1door",
        "gas_range_3burner",
        "gas_range_4burner",
        "convection_oven",
        "salamander",
        "multi_tier_shelf",
        "dishwasher_door_type",
        "dish_drying_rack",
        "hand_wash_sink",
        "two_comp_sink",
        "back_shelf",
    ],
    "cafeteria": [
        "work_table_medium",
        "work_table_medium",
        "wall_shelf",
        "overhead_shelf",
        "one_comp_sink",
        "table_refrigerator",
        "batt_table_refrigerator",
        "box45_refrigerator_freezer",
        "gas_range_3burner",
        "deep_fryer_double",
        "convection_oven",
        "griddle",
        "multi_tier_shelf",
        "dishwasher_door_type",
        "dish_drying_rack",
        "scrap_table",
        "hand_wash_sink",
        "two_comp_sink",
        "back_shelf",
    ],
    "ghost_kitchen": [
        "work_table_medium",
        "wall_shelf",
        "table_refrigerator",
        "box45_refrigerator_freezer",
        "gas_range_3burner",
        "deep_fryer_single",
        "convection_oven",
        "one_comp_sink",
        "hand_wash_sink",
        "overhead_shelf",
    ],
    "franchise": [
        "work_table_medium",
        "wall_shelf",
        "table_refrigerator",
        "gas_range_4burner",
        "deep_fryer_double",
        "griddle",
        "convection_oven",
        "one_comp_sink",
        "hand_wash_sink",
        "multi_tier_shelf",
        "box45_refrigerator_freezer",
        "overhead_shelf",
    ],
    "snack_bar": [
        "work_table_small",
        "wall_shelf",
        "table_refrigerator",
        "gas_range_4burner",
        "deep_fryer_single",
        "griddle",
        "one_comp_sink",
        "hand_wash_sink",
        "overhead_shelf",
    ],
    "bakery": [
        "work_table_medium",
        "work_table_medium",
        "wall_shelf",
        "overhead_shelf",
        "table_refrigerator",
        "reach_in_refrigerator_1door",
        "dry_storage_shelf",
        "dry_storage_shelf",
        "convection_oven",
        "convection_oven",
        "one_comp_sink",
        "hand_wash_sink",
        "multi_tier_shelf",
    ],
    "other": [
        "work_table_medium",
        "wall_shelf",
        "table_refrigerator",
        "one_comp_sink",
        "gas_range_4burner",
        "hand_wash_sink",
        "overhead_shelf",
        "multi_tier_shelf",
    ],
}

def get_equipment_for_restaurant(restaurant_type: str) -> List[EquipmentSpec]:
    """식당 유형에 맞는 장비 목록 반환"""
    equipment_ids = DEFAULT_EQUIPMENT_SETS.get(restaurant_type, DEFAULT_EQUIPMENT_SETS["casual"])
    return [EQUIPMENT_CATALOG[eq_id] for eq_id in equipment_ids if eq_id in EQUIPMENT_CATALOG]

def get_equipment_by_category(category: EquipmentCategory) -> List[EquipmentSpec]:
    """카테고리별 장비 목록 반환"""
    return [eq for eq in EQUIPMENT_CATALOG.values() if eq.category == category]


# 패턴 카테고리 → EquipmentCategory 매핑
_PATTERN_CAT_TO_ENUM = {
    "cooking": EquipmentCategory.COOKING,
    "prep": EquipmentCategory.PREPARATION,
    "preparation": EquipmentCategory.PREPARATION,
    "refrigeration": EquipmentCategory.STORAGE,
    "storage": EquipmentCategory.STORAGE,
    "dishwashing": EquipmentCategory.WASHING,
    "washing": EquipmentCategory.WASHING,
    "serving": EquipmentCategory.COOKING,
    "ventilation": EquipmentCategory.COOKING,
}

# 카테고리별 기본 장비 선택 우선순위
_CATEGORY_DEFAULTS = {
    EquipmentCategory.STORAGE: [
        "table_refrigerator",
        "box45_refrigerator_freezer",
        "wall_shelf",
        "overhead_shelf",
        "multi_tier_shelf",
        "back_shelf",
        "batt_table_refrigerator",
        "box45_refrigerator",
        "beverage_showcase",
        "broth_refrigerator",
        "ice_maker",
        "reach_in_refrigerator_2door",
        "reach_in_freezer_1door",
        "dry_storage_shelf",
        "reach_in_refrigerator_1door",
        "undercounter_refrigerator",
        "table_freezer",
    ],
    EquipmentCategory.PREPARATION: [
        "work_table_medium",
        "work_table_small",
        "prep_sink",
        "food_processor_station",
    ],
    EquipmentCategory.COOKING: [
        "gas_range_3burner",
        "gas_range_4burner",
        "deep_fryer_single",
        "convection_oven",
        "griddle",
        "deep_fryer_double",
        "salamander",
    ],
    EquipmentCategory.WASHING: [
        "one_comp_sink",
        "two_comp_sink",
        "hand_wash_sink",
        "dishwasher_undercounter",
        "dishwasher_pre_sink",
        "dish_drying_rack",
        "scrap_table",
        "drying_rack",
        "dishwasher_door_type",
    ],
}


def get_equipment_from_patterns(
    restaurant_type: str,
    kitchen_area_py: float = 8.0,
) -> List[EquipmentSpec]:
    """패턴 DB 기반 장비 목록 추천

    업종별 카테고리 분포 + 면적 기반 장비 수로 최적 장비 선택.
    PatternProvider 사용 불가 시 기존 하드코딩 세트로 fallback.

    Args:
        restaurant_type: 업종 코드 (korean, cafe, cafeteria 등)
        kitchen_area_py: 주방 면적 (평)

    Returns:
        추천 장비 목록
    """
    try:
        from ..patterns.provider import PatternProvider
        provider = PatternProvider()
    except Exception:
        return get_equipment_for_restaurant(restaurant_type)

    # 1. 예상 장비 수 산정
    target_count = provider.get_equipment_count_estimate(
        restaurant_type, kitchen_area_py
    )
    # 카탈로그 크기 내로 제한
    target_count = min(target_count, len(EQUIPMENT_CATALOG))

    # 2. 카테고리 분포 가져오기
    cat_dist = provider.get_category_distribution(restaurant_type)
    if not cat_dist:
        return get_equipment_for_restaurant(restaurant_type)

    # 3. 4구역 EquipmentCategory별 장비 수 계산
    zone_counts: Dict[EquipmentCategory, int] = {
        EquipmentCategory.STORAGE: 0,
        EquipmentCategory.PREPARATION: 0,
        EquipmentCategory.COOKING: 0,
        EquipmentCategory.WASHING: 0,
    }

    for cat_name, ratio in cat_dist.items():
        eq_cat = _PATTERN_CAT_TO_ENUM.get(cat_name)
        if eq_cat:
            zone_counts[eq_cat] += ratio

    # 비율 정규화 후 장비 수 할당
    total_ratio = sum(zone_counts.values())
    if total_ratio == 0:
        return get_equipment_for_restaurant(restaurant_type)

    equipment_list: List[EquipmentSpec] = []

    for eq_cat, ratio in zone_counts.items():
        count = max(1, round(target_count * ratio / total_ratio))
        defaults = _CATEGORY_DEFAULTS.get(eq_cat, [])

        for i, eq_id in enumerate(defaults):
            if len([e for e in equipment_list if e.category == eq_cat]) >= count:
                break
            if eq_id in EQUIPMENT_CATALOG:
                equipment_list.append(EQUIPMENT_CATALOG[eq_id])

    return equipment_list
