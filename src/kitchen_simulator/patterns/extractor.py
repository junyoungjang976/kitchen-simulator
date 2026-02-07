"""C2 패턴 추출 엔진 - 396건 실데이터에서 배치 패턴 분석"""
import json
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import (
    AreaBucket,
    BusinessTypePattern,
    CoOccurrenceEntry,
    EquipmentFrequency,
    PatternDatabase,
    ZoneEquipmentMapping,
)

# 구역명 정규화 매핑 (실데이터의 다양한 구역명 → 4구역 모델)
ZONE_NORMALIZATION = {
    "조리": "cooking",
    "cooking": "cooking",
    "조리구역": "cooking",
    "조리동선": "cooking",
    "조리 구역": "cooking",
    "조리영역": "cooking",
    "전처리": "preparation",
    "준비": "preparation",
    "준비구역": "preparation",
    "준비동선": "preparation",
    "준비 구역": "preparation",
    "작업구역": "preparation",
    "작업동선": "preparation",
    "작업 구역": "preparation",
    "전처리구역": "preparation",
    "전처리동선": "preparation",
    "prep": "preparation",
    "preparation": "preparation",
    "세척": "washing",
    "세척구역": "washing",
    "세척동선": "washing",
    "세척 구역": "washing",
    "퇴식": "washing",
    "퇴식구역": "washing",
    "퇴식동선": "washing",
    "washing": "washing",
    "저장": "storage",
    "저장구역": "storage",
    "저장동선": "storage",
    "저장 구역": "storage",
    "보관": "storage",
    "보관구역": "storage",
    "storage": "storage",
    "배식": "serving",
    "배식구역": "serving",
    "배식동선": "serving",
    "배식 구역": "serving",
    "serving": "serving",
    "배선": "serving",
    "배선구역": "serving",
}


def normalize_zone_name(raw_name: str) -> str:
    """구역명 정규화"""
    if not raw_name:
        return "other"

    cleaned = raw_name.strip().lower()

    # 직접 매핑
    if cleaned in ZONE_NORMALIZATION:
        return ZONE_NORMALIZATION[cleaned]

    # 부분 매칭
    for keyword, normalized in [
        ("조리", "cooking"),
        ("전처리", "preparation"),
        ("준비", "preparation"),
        ("작업", "preparation"),
        ("세척", "washing"),
        ("퇴식", "washing"),
        ("저장", "storage"),
        ("보관", "storage"),
        ("배식", "serving"),
        ("배선", "serving"),
    ]:
        if keyword in cleaned:
            return normalized

    return "other"


class PatternExtractor:
    """396건 실데이터에서 패턴 추출"""

    def __init__(self, dataset_path: str):
        self.dataset_path = Path(dataset_path)
        self.cases: List[dict] = []
        self._load_dataset()

    def _load_dataset(self):
        """dataset.json 로드"""
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.cases = data.get("cases", [])

    def extract_all(self) -> PatternDatabase:
        """전체 패턴 추출 실행"""
        total_equip = sum(
            len(c.get("equipment_list", [])) for c in self.cases
        )

        db = PatternDatabase(
            total_cases=len(self.cases),
            total_equipment_items=total_equip,
            business_type_patterns=self._extract_business_type_patterns(),
            co_occurrence_matrix=self._extract_co_occurrence(),
            zone_equipment_mappings=self._extract_zone_mappings(),
            area_patterns=self._extract_area_patterns(),
            global_category_distribution=self._extract_global_category_dist(),
            equipment_name_to_category=self._build_name_to_category_map(),
        )
        return db

    def _extract_business_type_patterns(self) -> Dict[str, BusinessTypePattern]:
        """업종별 패턴 추출"""
        # 업종별 그룹핑
        by_biz: Dict[str, List[dict]] = defaultdict(list)
        for c in self.cases:
            biz = c["basic_info"].get("business_type_category") or "other"
            by_biz[biz].append(c)

        patterns = {}
        for biz_type, cases in by_biz.items():
            # 평균 주방 면적
            areas = [
                c["basic_info"]["kitchen_area_py"]
                for c in cases
                if c["basic_info"].get("kitchen_area_py")
            ]
            avg_area = sum(areas) / len(areas) if areas else None

            # 장비 빈도
            equip_counter: Counter = Counter()
            equip_cat_counter: Counter = Counter()
            total_equip_count = 0
            for c in cases:
                eq_list = c.get("equipment_list", [])
                total_equip_count += len(eq_list)
                for eq in eq_list:
                    name = eq.get("name") or "(unknown)"
                    cat = eq.get("category") or "other"
                    equip_counter[f"{name}|{cat}"] += eq.get("quantity", 1)
                    equip_cat_counter[cat] += eq.get("quantity", 1)

            avg_equip = total_equip_count / len(cases) if cases else 0

            # 장비 빈도 리스트 (상위 30)
            freq_list = []
            for key, cnt in equip_counter.most_common(30):
                name, cat = key.rsplit("|", 1)
                freq_list.append(EquipmentFrequency(
                    equipment_name=name,
                    category=cat,
                    count=cnt,
                    ratio=round(cnt / len(cases), 3),
                ))

            # 카테고리 분포
            total_cat = sum(equip_cat_counter.values())
            cat_dist = {
                cat: round(cnt / total_cat, 3)
                for cat, cnt in equip_cat_counter.most_common()
            } if total_cat > 0 else {}

            # 주방 형태 분포
            shape_counter: Counter = Counter()
            for c in cases:
                dims = c.get("kitchen_dimensions") or {}
                shape = dims.get("shape_type") or "unknown"
                shape_counter[shape] += 1

            patterns[biz_type] = BusinessTypePattern(
                business_type=biz_type,
                case_count=len(cases),
                avg_kitchen_area_py=round(avg_area, 1) if avg_area else None,
                avg_equipment_count=round(avg_equip, 1),
                equipment_frequencies=freq_list,
                category_distribution=cat_dist,
                common_shapes=dict(shape_counter.most_common()),
            )

        return patterns

    def _extract_co_occurrence(self) -> List[CoOccurrenceEntry]:
        """장비 카테고리 공존 행렬 추출"""
        # 각 케이스에서 등장하는 카테고리 세트
        case_categories: List[set] = []
        for c in self.cases:
            cats = set()
            for eq in c.get("equipment_list", []):
                cat = eq.get("category")
                if cat:
                    cats.add(cat)
            if cats:
                case_categories.append(cats)

        # 모든 카테고리 쌍에 대해 공존 횟수 계산
        all_cats = sorted(set().union(*case_categories)) if case_categories else []
        total = len(case_categories)
        entries = []

        for cat_a, cat_b in combinations(all_cats, 2):
            co_count = sum(
                1 for cats in case_categories
                if cat_a in cats and cat_b in cats
            )
            if co_count > 0:
                entries.append(CoOccurrenceEntry(
                    equipment_a=cat_a,
                    equipment_b=cat_b,
                    co_occurrence_count=co_count,
                    co_occurrence_ratio=round(co_count / total, 3) if total > 0 else 0,
                ))

        entries.sort(key=lambda e: e.co_occurrence_count, reverse=True)
        return entries

    def _extract_zone_mappings(self) -> List[ZoneEquipmentMapping]:
        """구역-장비 매핑 통계"""
        # 정규화된 구역별 통계
        zone_data: Dict[str, dict] = defaultdict(lambda: {
            "variants": set(),
            "count": 0,
            "equip_cats": Counter(),
            "equip_counts": [],
        })

        # 장비명→카테고리 매핑 구축 (equipment_list에서)
        name_to_cat = self._build_name_to_category_map()

        for c in self.cases:
            for zone in c.get("zones", []):
                raw_name = zone.get("zone_name", "(unknown)")
                normalized = normalize_zone_name(raw_name)
                items = zone.get("equipment_items", [])

                zd = zone_data[normalized]
                zd["variants"].add(raw_name)
                zd["count"] += 1
                zd["equip_counts"].append(len(items))

                for item_name in items:
                    cat = name_to_cat.get(item_name, "other")
                    zd["equip_cats"][cat] += 1

        mappings = []
        for norm_name, zd in sorted(zone_data.items(), key=lambda x: x[1]["count"], reverse=True):
            avg_eq = sum(zd["equip_counts"]) / len(zd["equip_counts"]) if zd["equip_counts"] else 0
            mappings.append(ZoneEquipmentMapping(
                zone_name_normalized=norm_name,
                zone_name_variants=sorted(zd["variants"]),
                total_appearances=zd["count"],
                equipment_frequencies=dict(zd["equip_cats"].most_common()),
                avg_equipment_count=round(avg_eq, 1),
            ))

        return mappings

    def _extract_area_patterns(self) -> List[AreaBucket]:
        """면적 구간별 패턴 추출"""
        # 면적 구간: 0-3, 3-5, 5-8, 8-12, 12-20, 20+ (평)
        buckets_def = [
            (0, 3), (3, 5), (5, 8), (8, 12), (12, 20), (20, 50),
        ]

        buckets = []
        for area_min, area_max in buckets_def:
            bucket_cases = [
                c for c in self.cases
                if c["basic_info"].get("kitchen_area_py") is not None
                and area_min <= c["basic_info"]["kitchen_area_py"] < area_max
            ]

            if not bucket_cases:
                continue

            # 평균 장비 수
            equip_counts = [len(c.get("equipment_list", [])) for c in bucket_cases]
            avg_equip = sum(equip_counts) / len(equip_counts)

            # 카테고리 분포
            cat_counter: Counter = Counter()
            equip_name_counter: Counter = Counter()
            for c in bucket_cases:
                for eq in c.get("equipment_list", []):
                    cat = eq.get("category") or "other"
                    cat_counter[cat] += 1
                    equip_name_counter[eq.get("name") or "(unknown)"] += 1

            total_cat = sum(cat_counter.values())
            cat_dist = {
                cat: round(cnt / total_cat, 3)
                for cat, cnt in cat_counter.most_common()
            } if total_cat > 0 else {}

            # 상위 10 빈출 장비
            common_equip = [name for name, _ in equip_name_counter.most_common(10)]

            buckets.append(AreaBucket(
                area_min_py=area_min,
                area_max_py=area_max,
                case_count=len(bucket_cases),
                avg_equipment_count=round(avg_equip, 1),
                category_distribution=cat_dist,
                common_equipment=common_equip,
            ))

        return buckets

    def _extract_global_category_dist(self) -> Dict[str, float]:
        """전체 카테고리 분포"""
        cat_counter: Counter = Counter()
        for c in self.cases:
            for eq in c.get("equipment_list", []):
                cat = eq.get("category") or "other"
                cat_counter[cat] += 1

        total = sum(cat_counter.values())
        if total == 0:
            return {}
        return {
            cat: round(cnt / total, 4)
            for cat, cnt in cat_counter.most_common()
        }

    def _build_name_to_category_map(self) -> Dict[str, str]:
        """장비명→카테고리 매핑 사전 구축 (다수결)"""
        name_cats: Dict[str, Counter] = defaultdict(Counter)
        for c in self.cases:
            for eq in c.get("equipment_list", []):
                name = eq.get("name") or "(unknown)"
                cat = eq.get("category") or "other"
                name_cats[name][cat] += 1

        return {
            name: cats.most_common(1)[0][0]
            for name, cats in name_cats.items()
            if cats
        }

    def save(self, db: PatternDatabase, output_path: str):
        """패턴 DB를 JSON으로 저장"""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(db.model_dump_json(indent=2))


def main():
    """CLI 진입점"""
    import sys

    dataset_path = r"C:\Users\jangj\kitchen-simulator\data\extracted\dataset.json"
    output_path = r"C:\Users\jangj\kitchen-simulator\data\extracted\patterns.json"

    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    print(f"데이터셋 로드: {dataset_path}")
    extractor = PatternExtractor(dataset_path)
    print(f"  케이스 수: {len(extractor.cases)}")

    print("패턴 추출 중...")
    db = extractor.extract_all()

    print(f"\n=== 추출 결과 ===")
    print(f"  전체 케이스: {db.total_cases}")
    print(f"  전체 장비 항목: {db.total_equipment_items}")
    print(f"  업종 수: {len(db.business_type_patterns)}")
    print(f"  공존 행렬 항목: {len(db.co_occurrence_matrix)}")
    print(f"  구역 매핑: {len(db.zone_equipment_mappings)}")
    print(f"  면적 구간: {len(db.area_patterns)}")
    print(f"  장비명→카테고리 사전: {len(db.equipment_name_to_category)} 항목")

    # 업종별 요약
    print(f"\n=== 업종별 요약 ===")
    for biz, pat in sorted(db.business_type_patterns.items(), key=lambda x: x[1].case_count, reverse=True):
        print(f"  {biz}: {pat.case_count}건, 평균장비 {pat.avg_equipment_count}개, 면적 {pat.avg_kitchen_area_py}평")

    # 공존 행렬 상위 5
    print(f"\n=== 장비 카테고리 공존 (상위 5) ===")
    for entry in db.co_occurrence_matrix[:5]:
        print(f"  {entry.equipment_a} + {entry.equipment_b}: {entry.co_occurrence_ratio*100:.1f}%")

    # 구역 매핑
    print(f"\n=== 구역-장비 매핑 ===")
    for zm in db.zone_equipment_mappings:
        print(f"  {zm.zone_name_normalized}: {zm.total_appearances}회, 평균 {zm.avg_equipment_count}개 장비")

    # 면적 구간
    print(f"\n=== 면적 구간별 패턴 ===")
    for ab in db.area_patterns:
        print(f"  {ab.area_min_py}~{ab.area_max_py}평: {ab.case_count}건, 평균 {ab.avg_equipment_count}개 장비")

    extractor.save(db, output_path)
    print(f"\n저장 완료: {output_path}")


if __name__ == "__main__":
    main()
