"""유사도 계산 함수들"""
import math
from typing import Dict, List, Tuple
from collections import Counter


def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """두 딕셔너리 벡터의 코사인 유사도 (0~1)"""
    all_keys = set(vec_a.keys()) | set(vec_b.keys())
    if not all_keys:
        return 0.0

    dot = sum(vec_a.get(k, 0) * vec_b.get(k, 0) for k in all_keys)
    mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """자카드 유사도 (0~1)"""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0

    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def count_accuracy(generated_count: int, real_count: int) -> float:
    """장비 수 정확도 (0~1, 가우시안 기반)

    정확히 일치하면 1.0, 차이가 클수록 감소
    σ=0.3 → 30% 차이에서 ~0.6
    """
    if real_count == 0:
        return 1.0 if generated_count == 0 else 0.0

    ratio_diff = abs(generated_count - real_count) / max(real_count, 1)
    return math.exp(-(ratio_diff ** 2) / (2 * 0.3 ** 2))


def category_distribution_from_equipment(
    equipment_list: List[dict],
) -> Dict[str, float]:
    """장비 목록에서 카테고리 분포 추출 (비율)"""
    cat_counter = Counter()
    for eq in equipment_list:
        cat = eq.get("category") or "other"
        cat_counter[cat] += eq.get("quantity", 1)

    total = sum(cat_counter.values())
    if total == 0:
        return {}

    return {cat: cnt / total for cat, cnt in cat_counter.items()}


def category_distribution_from_generated(
    equipment_list: List,  # List[GeneratedEquipment]
) -> Dict[str, float]:
    """GeneratedEquipment 리스트에서 카테고리 분포 추출"""
    cat_counter = Counter()
    for eq in equipment_list:
        cat_counter[eq.category] += eq.quantity

    total = sum(cat_counter.values())
    if total == 0:
        return {}

    return {cat: cnt / total for cat, cnt in cat_counter.items()}


def zone_ratio_from_zones(zones: List[dict]) -> Dict[str, float]:
    """실 데이터 구역 목록에서 구역 비율 추출 (장비 수 기반)"""
    from ..patterns.extractor import normalize_zone_name

    zone_counter = Counter()
    for zone in zones:
        name = normalize_zone_name(zone.get("zone_name", ""))
        items = zone.get("equipment_items", [])
        zone_counter[name] += len(items)

    total = sum(zone_counter.values())
    if total == 0:
        return {}

    return {zone: cnt / total for zone, cnt in zone_counter.items()}


def equipment_names_from_real(equipment_list: List[dict]) -> set:
    """실 데이터에서 장비명 세트 추출 (정규화)"""
    names = set()
    for eq in equipment_list:
        name = eq.get("name", "").strip()
        if name and name != "(unknown)":
            names.add(name)
    return names


def equipment_names_from_generated(equipment_list: List) -> set:
    """GeneratedEquipment에서 장비명 세트 추출"""
    names = set()
    for eq in equipment_list:
        name = eq.equipment_name.strip()
        if name and name != "(unknown)":
            names.add(name)
    return names
