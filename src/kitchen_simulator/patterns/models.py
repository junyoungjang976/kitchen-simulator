"""C2 패턴 데이터 모델 - 추출된 패턴의 정형 구조"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime


class EquipmentFrequency(BaseModel):
    """업종별 장비 출현 빈도"""
    equipment_name: str = Field(description="장비명")
    category: str = Field(description="장비 카테고리")
    count: int = Field(description="등장 횟수")
    ratio: float = Field(description="해당 업종 내 등장 비율 (0~1)")


class BusinessTypePattern(BaseModel):
    """업종별 패턴"""
    business_type: str = Field(description="업종 카테고리")
    case_count: int = Field(description="해당 업종 케이스 수")
    avg_kitchen_area_py: Optional[float] = Field(default=None, description="평균 주방 면적(평)")
    avg_equipment_count: float = Field(description="평균 장비 수")
    equipment_frequencies: List[EquipmentFrequency] = Field(
        default_factory=list, description="장비 빈도 (내림차순)"
    )
    category_distribution: Dict[str, float] = Field(
        default_factory=dict, description="카테고리별 비율"
    )
    common_shapes: Dict[str, int] = Field(
        default_factory=dict, description="주방 형태 분포"
    )


class CoOccurrenceEntry(BaseModel):
    """장비 공존 항목"""
    equipment_a: str = Field(description="장비 A 카테고리")
    equipment_b: str = Field(description="장비 B 카테고리")
    co_occurrence_count: int = Field(description="함께 등장한 케이스 수")
    co_occurrence_ratio: float = Field(description="공존 비율 (0~1)")


class ZoneEquipmentMapping(BaseModel):
    """구역-장비 매핑 통계"""
    zone_name_normalized: str = Field(description="정규화된 구역명")
    zone_name_variants: List[str] = Field(
        default_factory=list, description="원본 구역명 변형들"
    )
    total_appearances: int = Field(description="구역 등장 횟수")
    equipment_frequencies: Dict[str, int] = Field(
        default_factory=dict, description="구역 내 장비 카테고리별 빈도"
    )
    avg_equipment_count: float = Field(description="구역 내 평균 장비 수")


class AreaBucket(BaseModel):
    """면적 구간별 패턴"""
    area_min_py: float = Field(description="면적 하한 (평)")
    area_max_py: float = Field(description="면적 상한 (평)")
    case_count: int = Field(description="케이스 수")
    avg_equipment_count: float = Field(description="평균 장비 수")
    category_distribution: Dict[str, float] = Field(
        default_factory=dict, description="카테고리별 평균 비율"
    )
    common_equipment: List[str] = Field(
        default_factory=list, description="빈출 장비 (상위 10)"
    )


class PatternDatabase(BaseModel):
    """C2 패턴 데이터베이스 - 전체 추출 결과"""
    version: str = Field(default="1.0.0", description="패턴 DB 버전")
    created_at: datetime = Field(default_factory=datetime.now)
    total_cases: int = Field(description="분석 케이스 수")
    total_equipment_items: int = Field(description="전체 장비 항목 수")

    # 업종별 패턴
    business_type_patterns: Dict[str, BusinessTypePattern] = Field(
        default_factory=dict, description="업종별 패턴"
    )

    # 장비 카테고리 공존 행렬
    co_occurrence_matrix: List[CoOccurrenceEntry] = Field(
        default_factory=list, description="장비 카테고리 공존 행렬"
    )

    # 구역-장비 매핑
    zone_equipment_mappings: List[ZoneEquipmentMapping] = Field(
        default_factory=list, description="구역별 장비 매핑"
    )

    # 면적 구간별 패턴
    area_patterns: List[AreaBucket] = Field(
        default_factory=list, description="면적 구간별 패턴"
    )

    # 글로벌 통계
    global_category_distribution: Dict[str, float] = Field(
        default_factory=dict, description="전체 카테고리 분포"
    )
    equipment_name_to_category: Dict[str, str] = Field(
        default_factory=dict, description="장비명→카테고리 매핑 사전"
    )
