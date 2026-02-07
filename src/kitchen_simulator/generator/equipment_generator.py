"""패턴 기반 장비 리스트 생성기"""
import random
from typing import Dict, List, Optional, Tuple

from .models import GeneratedEquipment, SimilarCase
from .case_retriever import CaseRetriever
from ..patterns.provider import PatternProvider
from ..data.equipment_catalog import EQUIPMENT_CATALOG, EquipmentCategory

# 한국어 장비명 → 카탈로그 ID 매핑 (패턴 데이터의 장비를 카탈로그에 연결)
# 패턴 데이터의 한국어 장비명을 카탈로그의 표준 장비로 매핑
PATTERN_TO_CATALOG = {
    # 냉장/냉동
    "업소용냉장고": "reach_in_refrigerator_2door",
    "업소용 냉장고": "reach_in_refrigerator_2door",
    "냉장고": "reach_in_refrigerator_2door",
    "2도어냉장고": "reach_in_refrigerator_2door",
    "1도어냉장고": "reach_in_refrigerator_1door",
    "냉동고": "reach_in_freezer_1door",
    "업소용냉동고": "reach_in_freezer_1door",
    "테이블냉장고": "undercounter_refrigerator",
    "테이블냉동고": "undercounter_refrigerator",
    "언더카운터냉장고": "undercounter_refrigerator",
    "김치냉장고": "reach_in_refrigerator_1door",

    # 작업대/전처리
    "작업대": "work_table_medium",
    "2단작업대": "work_table_medium",
    "3단작업대": "work_table_large",
    "작업대(대)": "work_table_large",
    "작업대(소)": "work_table_small",
    "전처리대": "work_table_medium",
    "준비대": "work_table_medium",
    "선반": "dry_storage_shelf",
    "벽선반": "dry_storage_shelf",
    "상부선반": "dry_storage_shelf",

    # 싱크대
    "싱크대": "three_compartment_sink",
    "3조싱크대": "three_compartment_sink",
    "2조싱크대": "three_compartment_sink",
    "1조싱크대": "prep_sink",
    "전처리싱크": "prep_sink",
    "손세정대": "hand_wash_sink",
    "손세척싱크": "hand_wash_sink",
    "핸드워시": "hand_wash_sink",

    # 조리 장비
    "가스레인지": "gas_range_6burner",
    "가스렌지": "gas_range_6burner",
    "4구가스레인지": "gas_range_4burner",
    "6구가스레인지": "gas_range_6burner",
    "튀김기": "deep_fryer_single",
    "더블튀김기": "deep_fryer_double",
    "오븐": "convection_oven",
    "컨벡션오븐": "convection_oven",
    "그리들": "griddle",
    "철판": "griddle",
    "샐러맨더": "salamander",

    # 세척
    "식기세척기": "dishwasher_undercounter",
    "도어식기세척기": "dishwasher_door_type",
    "건조대": "drying_rack",
    "건조선반": "drying_rack",

    # 푸드프로세서
    "식품가공기": "food_processor_station",
    "푸드프로세서": "food_processor_station",
}

# 카테고리별 기본 필수 장비 (최소 세트)
CATEGORY_ESSENTIALS = {
    "storage": ["reach_in_refrigerator_2door", "reach_in_freezer_1door"],
    "preparation": ["work_table_medium"],
    "cooking": ["gas_range_4burner"],
    "washing": ["three_compartment_sink", "hand_wash_sink"],
}


class EquipmentGenerator:
    """패턴 데이터 + 유사 사례 기반 장비 리스트 생성"""

    def __init__(self, seed: Optional[int] = None):
        self.provider = PatternProvider()
        self.retriever = CaseRetriever()
        self.rng = random.Random(seed)

    def generate(
        self,
        business_type: str,
        kitchen_area_py: float,
        shape_type: Optional[str] = None,
        top_k_cases: int = 5,
    ) -> Tuple[List[GeneratedEquipment], List[SimilarCase]]:
        """장비 리스트 생성

        3단계 파이프라인:
        1. 유사 사례 검색 → 장비 합집합 추출
        2. 업종 패턴 빈도 → 확률적 장비 선택
        3. 필수 장비 보장 + 공존 규칙 검증

        Args:
            business_type: 업종
            kitchen_area_py: 주방 면적 (평)
            shape_type: 주방 형태
            top_k_cases: 유사 사례 수

        Returns:
            (생성된 장비 리스트, 유사 사례 리스트)
        """
        # 0. 목표 장비 수 결정
        target_count = self.provider.get_equipment_count_estimate(
            business_type, kitchen_area_py
        )

        # 1. 유사 사례 검색
        similar_cases = self.retriever.find_similar(
            business_type, kitchen_area_py, shape_type, top_k_cases
        )

        # 2. 패턴 기반 장비 후보 생성
        candidates = self._generate_candidates(business_type, similar_cases)

        # 3. 목표 수량에 맞춰 선택
        selected = self._select_equipment(candidates, target_count)

        # 4. 필수 장비 보장
        selected = self._ensure_essentials(selected)

        # 5. 카탈로그 매핑
        for eq in selected:
            if not eq.catalog_id:
                eq.catalog_id = self._map_to_catalog(eq.equipment_name, eq.category)

        return selected, similar_cases

    def _generate_candidates(
        self,
        business_type: str,
        similar_cases: List[SimilarCase],
    ) -> List[GeneratedEquipment]:
        """후보 장비 목록 생성 (패턴 + 유사사례 합산)"""
        candidates: Dict[str, GeneratedEquipment] = {}

        # 소스 1: 업종 패턴 빈도 (상위 20)
        top_equipment = self.provider.get_top_equipment(business_type, top_n=20)
        for name, category, ratio in top_equipment:
            if name and name != "(unknown)":
                candidates[name] = GeneratedEquipment(
                    equipment_name=name,
                    category=category,
                    quantity=1,
                    confidence=ratio,
                    source="pattern",
                    catalog_id=self._map_to_catalog(name, category),
                )

        # 소스 2: 유사 사례 장비 합집합
        if similar_cases:
            case_equipment = self.retriever.get_equipment_union(similar_cases)
            for name, (category, weight) in case_equipment.items():
                if name in candidates:
                    # 이미 패턴에 있으면 신뢰도 부스트
                    old = candidates[name]
                    candidates[name] = GeneratedEquipment(
                        equipment_name=name,
                        category=category,
                        quantity=old.quantity,
                        confidence=min(1.0, old.confidence + weight * 0.3),
                        source="pattern+similar_case",
                        catalog_id=old.catalog_id,
                    )
                elif name and name != "(unknown)":
                    candidates[name] = GeneratedEquipment(
                        equipment_name=name,
                        category=category,
                        quantity=1,
                        confidence=weight * 0.5,
                        source="similar_case",
                        catalog_id=self._map_to_catalog(name, category),
                    )

        return list(candidates.values())

    def _select_equipment(
        self,
        candidates: List[GeneratedEquipment],
        target_count: int,
    ) -> List[GeneratedEquipment]:
        """목표 수량에 맞춰 장비 선택 (신뢰도 가중 확률)"""
        if not candidates:
            return []

        # 신뢰도 내림차순 정렬
        candidates.sort(key=lambda e: e.confidence, reverse=True)

        # 카탈로그 매핑이 있는 장비 우선
        mapped = [c for c in candidates if c.catalog_id]
        unmapped = [c for c in candidates if not c.catalog_id]

        selected = []

        # 매핑된 장비 우선 선택
        for eq in mapped:
            if len(selected) >= target_count:
                break
            selected.append(eq)

        # 부족하면 매핑 안 된 장비도 추가
        for eq in unmapped:
            if len(selected) >= target_count:
                break
            selected.append(eq)

        return selected

    def _ensure_essentials(
        self,
        selected: List[GeneratedEquipment],
    ) -> List[GeneratedEquipment]:
        """필수 장비가 없으면 추가"""
        existing_catalog_ids = {eq.catalog_id for eq in selected if eq.catalog_id}

        for category, essential_ids in CATEGORY_ESSENTIALS.items():
            # 해당 카테고리에 이미 장비가 있는지 확인
            has_category = any(
                eq.catalog_id and eq.catalog_id in {eid for eid in essential_ids}
                or eq.category == category
                for eq in selected
            )

            if not has_category:
                # 필수 장비 중 첫 번째 추가
                for eid in essential_ids:
                    if eid not in existing_catalog_ids and eid in EQUIPMENT_CATALOG:
                        spec = EQUIPMENT_CATALOG[eid]
                        selected.append(GeneratedEquipment(
                            equipment_name=spec.name_ko,
                            category=category,
                            quantity=1,
                            confidence=0.5,
                            source="essential",
                            catalog_id=eid,
                        ))
                        existing_catalog_ids.add(eid)
                        break

        return selected

    def _map_to_catalog(self, equipment_name: str, category: str) -> Optional[str]:
        """한국어 장비명을 카탈로그 ID로 매핑"""
        # 1. 직접 매핑
        if equipment_name in PATTERN_TO_CATALOG:
            return PATTERN_TO_CATALOG[equipment_name]

        # 2. 부분 문자열 매칭
        name_lower = equipment_name.lower().strip()
        for pattern_name, catalog_id in PATTERN_TO_CATALOG.items():
            if pattern_name in name_lower or name_lower in pattern_name:
                return catalog_id

        # 3. 카테고리 기반 기본 매핑
        CATEGORY_DEFAULTS = {
            "cooking": "gas_range_4burner",
            "prep": "work_table_medium",
            "preparation": "work_table_medium",
            "refrigeration": "reach_in_refrigerator_1door",
            "storage": "dry_storage_shelf",
            "dishwashing": "three_compartment_sink",
            "washing": "three_compartment_sink",
        }
        return CATEGORY_DEFAULTS.get(category)
