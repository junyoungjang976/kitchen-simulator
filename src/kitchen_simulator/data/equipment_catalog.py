"""장비 카탈로그 - 식당 주방 표준 장비 규격"""
from typing import Dict, List
from ..domain.equipment import EquipmentSpec, EquipmentCategory

# 저장 구역 장비
STORAGE_EQUIPMENT: List[EquipmentSpec] = [
    EquipmentSpec(
        id="reach_in_refrigerator_1door",
        name="Reach-in Refrigerator (1-door)",
        name_ko="업소용 냉장고 1도어",
        category=EquipmentCategory.STORAGE,
        width=0.66, depth=0.76, height=2.0,
        clearance_front=0.9,
        requires_wall=True,
    ),
    EquipmentSpec(
        id="reach_in_refrigerator_2door",
        name="Reach-in Refrigerator (2-door)",
        name_ko="업소용 냉장고 2도어",
        category=EquipmentCategory.STORAGE,
        width=1.32, depth=0.76, height=2.0,
        clearance_front=0.9,
        requires_wall=True,
    ),
    EquipmentSpec(
        id="reach_in_freezer_1door",
        name="Reach-in Freezer (1-door)",
        name_ko="업소용 냉동고 1도어",
        category=EquipmentCategory.STORAGE,
        width=0.66, depth=0.76, height=2.0,
        clearance_front=0.9,
        requires_wall=True,
    ),
    EquipmentSpec(
        id="dry_storage_shelf",
        name="Dry Storage Shelf",
        name_ko="건조 저장 선반",
        category=EquipmentCategory.STORAGE,
        width=1.2, depth=0.45, height=1.8,
        clearance_front=0.6,
        requires_wall=True,
    ),
    EquipmentSpec(
        id="undercounter_refrigerator",
        name="Undercounter Refrigerator",
        name_ko="언더카운터 냉장고",
        category=EquipmentCategory.STORAGE,
        width=0.7, depth=0.61, height=0.86,
        clearance_front=0.6,
    ),
]

# 전처리/준비 구역 장비
PREPARATION_EQUIPMENT: List[EquipmentSpec] = [
    EquipmentSpec(
        id="work_table_small",
        name="Work Table (small)",
        name_ko="작업대 소형",
        category=EquipmentCategory.PREPARATION,
        width=0.9, depth=0.6, height=0.86,
        clearance_front=0.9,
    ),
    EquipmentSpec(
        id="work_table_medium",
        name="Work Table (medium)",
        name_ko="작업대 중형",
        category=EquipmentCategory.PREPARATION,
        width=1.5, depth=0.75, height=0.86,
        clearance_front=0.9,
    ),
    EquipmentSpec(
        id="work_table_large",
        name="Work Table (large)",
        name_ko="작업대 대형",
        category=EquipmentCategory.PREPARATION,
        width=2.0, depth=0.75, height=0.86,
        clearance_front=0.9,
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
    ),
    EquipmentSpec(
        id="food_processor_station",
        name="Food Processor Station",
        name_ko="식품 가공기 스테이션",
        category=EquipmentCategory.PREPARATION,
        width=0.6, depth=0.5, height=0.86,
        clearance_front=0.6,
    ),
]

# 조리 구역 장비
COOKING_EQUIPMENT: List[EquipmentSpec] = [
    EquipmentSpec(
        id="gas_range_4burner",
        name="Gas Range (4-burner)",
        name_ko="가스레인지 4구",
        category=EquipmentCategory.COOKING,
        width=0.6, depth=0.7, height=0.91,
        clearance_front=0.91, clearance_sides=0.46,
        requires_ventilation=True,
    ),
    EquipmentSpec(
        id="gas_range_6burner",
        name="Gas Range (6-burner)",
        name_ko="가스레인지 6구",
        category=EquipmentCategory.COOKING,
        width=0.91, depth=0.7, height=0.91,
        clearance_front=0.91, clearance_sides=0.46,
        requires_ventilation=True,
    ),
    EquipmentSpec(
        id="deep_fryer_single",
        name="Deep Fryer (single)",
        name_ko="튀김기 단일",
        category=EquipmentCategory.COOKING,
        width=0.4, depth=0.76, height=1.1,
        clearance_front=0.91,
        requires_ventilation=True,
    ),
    EquipmentSpec(
        id="deep_fryer_double",
        name="Deep Fryer (double)",
        name_ko="튀김기 더블",
        category=EquipmentCategory.COOKING,
        width=0.8, depth=0.76, height=1.1,
        clearance_front=0.91,
        requires_ventilation=True,
    ),
    EquipmentSpec(
        id="convection_oven",
        name="Convection Oven",
        name_ko="컨벡션 오븐",
        category=EquipmentCategory.COOKING,
        width=0.9, depth=0.76, height=1.5,
        clearance_front=1.2,
        requires_ventilation=True,
    ),
    EquipmentSpec(
        id="griddle",
        name="Griddle",
        name_ko="그리들",
        category=EquipmentCategory.COOKING,
        width=0.9, depth=0.6, height=0.91,
        clearance_front=0.91,
        requires_ventilation=True,
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
    ),
]

# 세척 구역 장비
WASHING_EQUIPMENT: List[EquipmentSpec] = [
    EquipmentSpec(
        id="three_compartment_sink",
        name="3-Compartment Sink",
        name_ko="3조 싱크대",
        category=EquipmentCategory.WASHING,
        width=1.8, depth=0.6, height=1.1,
        clearance_front=0.9,
        requires_water=True,
        requires_drain=True,
    ),
    EquipmentSpec(
        id="dishwasher_undercounter",
        name="Undercounter Dishwasher",
        name_ko="언더카운터 식기세척기",
        category=EquipmentCategory.WASHING,
        width=0.6, depth=0.6, height=0.86,
        clearance_front=0.9,
        requires_water=True,
        requires_drain=True,
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
    ),
    EquipmentSpec(
        id="drying_rack",
        name="Drying Rack",
        name_ko="건조대",
        category=EquipmentCategory.WASHING,
        width=1.0, depth=0.5, height=1.7,
        clearance_front=0.6,
        requires_wall=True,
    ),
    EquipmentSpec(
        id="hand_wash_sink",
        name="Hand Wash Sink",
        name_ko="손 세척 싱크",
        category=EquipmentCategory.WASHING,
        width=0.4, depth=0.35, height=0.86,
        clearance_front=0.6,
        requires_water=True,
        requires_drain=True,
        requires_wall=True,
    ),
]

# 전체 카탈로그
EQUIPMENT_CATALOG: Dict[str, EquipmentSpec] = {
    eq.id: eq
    for eq_list in [STORAGE_EQUIPMENT, PREPARATION_EQUIPMENT,
                    COOKING_EQUIPMENT, WASHING_EQUIPMENT]
    for eq in eq_list
}

# 식당 유형별 기본 장비 세트
DEFAULT_EQUIPMENT_SETS = {
    "fast_food": [
        "reach_in_refrigerator_2door",
        "reach_in_freezer_1door",
        "work_table_medium",
        "gas_range_4burner",
        "deep_fryer_double",
        "griddle",
        "three_compartment_sink",
        "hand_wash_sink",
    ],
    "casual": [
        "reach_in_refrigerator_2door",
        "reach_in_freezer_1door",
        "dry_storage_shelf",
        "work_table_large",
        "prep_sink",
        "gas_range_6burner",
        "deep_fryer_single",
        "convection_oven",
        "three_compartment_sink",
        "dishwasher_undercounter",
        "hand_wash_sink",
    ],
    "fine_dining": [
        "reach_in_refrigerator_2door",
        "reach_in_refrigerator_2door",
        "reach_in_freezer_1door",
        "dry_storage_shelf",
        "dry_storage_shelf",
        "work_table_large",
        "work_table_large",
        "prep_sink",
        "food_processor_station",
        "gas_range_6burner",
        "gas_range_4burner",
        "convection_oven",
        "salamander",
        "three_compartment_sink",
        "dishwasher_door_type",
        "drying_rack",
        "hand_wash_sink",
    ],
    "cafeteria": [
        "reach_in_refrigerator_2door",
        "reach_in_refrigerator_2door",
        "reach_in_freezer_1door",
        "dry_storage_shelf",
        "dry_storage_shelf",
        "work_table_large",
        "work_table_large",
        "work_table_medium",
        "prep_sink",
        "gas_range_6burner",
        "deep_fryer_double",
        "convection_oven",
        "griddle",
        "three_compartment_sink",
        "dishwasher_door_type",
        "drying_rack",
        "hand_wash_sink",
        "hand_wash_sink",
    ],
    "ghost_kitchen": [
        "reach_in_refrigerator_2door",
        "reach_in_freezer_1door",
        "work_table_medium",
        "gas_range_6burner",
        "deep_fryer_single",
        "convection_oven",
        "three_compartment_sink",
        "hand_wash_sink",
    ],
}

def get_equipment_for_restaurant(restaurant_type: str) -> List[EquipmentSpec]:
    """식당 유형에 맞는 장비 목록 반환"""
    equipment_ids = DEFAULT_EQUIPMENT_SETS.get(restaurant_type, DEFAULT_EQUIPMENT_SETS["casual"])
    return [EQUIPMENT_CATALOG[eq_id] for eq_id in equipment_ids if eq_id in EQUIPMENT_CATALOG]

def get_equipment_by_category(category: EquipmentCategory) -> List[EquipmentSpec]:
    """카테고리별 장비 목록 반환"""
    return [eq for eq in EQUIPMENT_CATALOG.values() if eq.category == category]
