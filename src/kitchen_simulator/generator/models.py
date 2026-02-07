"""C3 생성 결과 데이터 모델"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Tuple


class SimilarCase(BaseModel):
    """유사 사례 검색 결과"""
    case_number: int = Field(description="사례 번호")
    business_type: str = Field(description="업종")
    kitchen_area_py: Optional[float] = Field(default=None, description="주방 면적(평)")
    equipment_count: int = Field(description="장비 수")
    similarity_score: float = Field(description="유사도 점수 (0~1)")
    equipment_names: List[str] = Field(default_factory=list, description="장비명 목록")
    zone_names: List[str] = Field(default_factory=list, description="구역명 목록")


class GeneratedEquipment(BaseModel):
    """생성된 장비 항목"""
    equipment_name: str = Field(description="장비명 (한국어, 패턴 데이터 원본)")
    category: str = Field(description="카테고리")
    quantity: int = Field(default=1, description="수량")
    confidence: float = Field(description="신뢰도 (0~1, 패턴 출현비율 기반)")
    source: str = Field(default="pattern", description="출처: pattern/similar_case/co_occurrence")
    catalog_id: Optional[str] = Field(default=None, description="매칭된 카탈로그 장비 ID")


class GenerationResult(BaseModel):
    """C3 생성 결과"""
    business_type: str = Field(description="입력 업종")
    kitchen_area_py: float = Field(description="입력 면적(평)")

    # 유사 사례
    similar_cases: List[SimilarCase] = Field(
        default_factory=list, description="검색된 유사 사례"
    )

    # 생성된 장비 리스트
    generated_equipment: List[GeneratedEquipment] = Field(
        default_factory=list, description="생성된 장비 목록"
    )

    # 추천 구역 비율
    recommended_zone_ratios: Dict[str, float] = Field(
        default_factory=dict, description="추천 구역 비율"
    )

    # 메타데이터
    generation_method: str = Field(
        default="retrieval_augmented_statistical",
        description="생성 방식"
    )
    pattern_coverage: float = Field(
        default=0.0, description="패턴 데이터 커버리지 (0~1)"
    )
