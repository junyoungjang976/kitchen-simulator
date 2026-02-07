"""C5 평가 결과 데이터 모델"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class SimilarityMetrics(BaseModel):
    """유사도 세부 지표"""
    equipment_category_similarity: float = Field(
        description="장비 카테고리 분포 유사도 (코사인, 0~1)"
    )
    equipment_name_overlap: float = Field(
        description="장비명 겹침 비율 (Jaccard, 0~1)"
    )
    equipment_count_accuracy: float = Field(
        description="장비 수 정확도 (0~1, 1=정확히 일치)"
    )
    zone_ratio_similarity: float = Field(
        description="구역 비율 유사도 (코사인, 0~1)"
    )
    overall_similarity: float = Field(
        description="종합 유사도 점수 (0~100)"
    )


class CaseComparison(BaseModel):
    """개별 사례와의 비교 결과"""
    case_number: int
    business_type: str
    kitchen_area_py: Optional[float]
    similarity_metrics: SimilarityMetrics
    matched_equipment: List[str] = Field(
        default_factory=list, description="일치하는 장비명"
    )
    missing_equipment: List[str] = Field(
        default_factory=list, description="실 사례에는 있지만 생성에 없는 장비"
    )
    extra_equipment: List[str] = Field(
        default_factory=list, description="생성에는 있지만 실 사례에 없는 장비"
    )


class EvaluationResult(BaseModel):
    """단일 생성 결과 평가"""
    business_type: str
    kitchen_area_py: float

    # 유사 사례와의 평균 유사도
    avg_similarity: SimilarityMetrics

    # 개별 사례 비교
    case_comparisons: List[CaseComparison] = Field(default_factory=list)

    # 배치 품질 (기존 ScoringEngine 결과)
    layout_score: Optional[float] = Field(
        default=None, description="배치 최적화 점수 (0~100)"
    )

    # 최종 평가
    final_score: float = Field(
        description="최종 종합 점수 (유사도 60% + 배치품질 40%)"
    )
    grade: str = Field(description="등급: S/A/B/C/D")


class EvaluationReport(BaseModel):
    """다중 생성 결과 평가 리포트"""
    total_evaluations: int
    avg_final_score: float
    avg_similarity: float
    avg_layout_score: float
    grade_distribution: Dict[str, int] = Field(default_factory=dict)
    evaluations: List[EvaluationResult] = Field(default_factory=list)

    # 업종별 성능
    by_business_type: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="업종별 {avg_similarity, avg_layout_score, avg_final_score}"
    )
