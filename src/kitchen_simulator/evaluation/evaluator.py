"""C5 평가 엔진 - 생성 결과와 실데이터 비교"""
from typing import Dict, List, Optional

from .models import (
    CaseComparison,
    EvaluationReport,
    EvaluationResult,
    SimilarityMetrics,
)
from .metrics import (
    category_distribution_from_equipment,
    category_distribution_from_generated,
    cosine_similarity,
    count_accuracy,
    equipment_names_from_generated,
    equipment_names_from_real,
    jaccard_similarity,
    zone_ratio_from_zones,
)
from ..generator.models import GenerationResult
from ..generator.case_retriever import CaseRetriever


# 유사도 가중치
SIMILARITY_WEIGHTS = {
    "equipment_category": 0.30,  # 카테고리 분포
    "equipment_name": 0.25,      # 장비명 겹침
    "equipment_count": 0.20,     # 장비 수
    "zone_ratio": 0.25,          # 구역 비율
}

# 최종 점수 가중치
FINAL_WEIGHTS = {
    "similarity": 0.60,  # 유사도
    "layout": 0.40,      # 배치 품질
}

# 등급 기준
GRADE_THRESHOLDS = {
    "S": 90,
    "A": 80,
    "B": 70,
    "C": 60,
    "D": 0,
}


class Evaluator:
    """생성 결과 평가기"""

    def __init__(self):
        self.retriever = CaseRetriever()

    def evaluate(
        self,
        gen_result: GenerationResult,
        layout_score: Optional[float] = None,
        compare_top_k: int = 5,
    ) -> EvaluationResult:
        """단일 생성 결과 평가

        Args:
            gen_result: C3 생성 결과
            layout_score: 배치 최적화 점수 (0~100)
            compare_top_k: 비교할 유사 사례 수

        Returns:
            EvaluationResult
        """
        # 유사 사례 가져오기 (gen_result에 이미 있거나 새로 검색)
        similar_cases = gen_result.similar_cases
        if not similar_cases:
            similar_cases = self.retriever.find_similar(
                gen_result.business_type,
                gen_result.kitchen_area_py,
                top_k=compare_top_k,
            )

        # 각 유사 사례와 비교
        comparisons = []
        for sc in similar_cases[:compare_top_k]:
            original = self.retriever._find_case(sc.case_number)
            if not original:
                continue

            comp = self._compare_with_case(gen_result, original)
            comparisons.append(comp)

        # 평균 유사도 계산
        avg_sim = self._average_metrics(comparisons)

        # 최종 점수 = 유사도 60% + 배치품질 40%
        sim_score = avg_sim.overall_similarity
        layout = layout_score if layout_score is not None else 50.0
        final = sim_score * FINAL_WEIGHTS["similarity"] + layout * FINAL_WEIGHTS["layout"]

        # 등급 결정
        grade = "D"
        for g, threshold in GRADE_THRESHOLDS.items():
            if final >= threshold:
                grade = g
                break

        return EvaluationResult(
            business_type=gen_result.business_type,
            kitchen_area_py=gen_result.kitchen_area_py,
            avg_similarity=avg_sim,
            case_comparisons=comparisons,
            layout_score=layout_score,
            final_score=round(final, 1),
            grade=grade,
        )

    def evaluate_batch(
        self,
        results: List[tuple],  # List[(GenerationResult, layout_score)]
    ) -> EvaluationReport:
        """다중 생성 결과 일괄 평가"""
        evaluations = []
        for gen_result, layout_score in results:
            ev = self.evaluate(gen_result, layout_score)
            evaluations.append(ev)

        if not evaluations:
            return EvaluationReport(
                total_evaluations=0,
                avg_final_score=0,
                avg_similarity=0,
                avg_layout_score=0,
            )

        # 집계
        avg_final = sum(e.final_score for e in evaluations) / len(evaluations)
        avg_sim = sum(e.avg_similarity.overall_similarity for e in evaluations) / len(evaluations)
        avg_layout = sum(
            (e.layout_score or 0) for e in evaluations
        ) / len(evaluations)

        # 등급 분포
        grade_dist = {}
        for e in evaluations:
            grade_dist[e.grade] = grade_dist.get(e.grade, 0) + 1

        # 업종별 성능
        by_biz: Dict[str, List[EvaluationResult]] = {}
        for e in evaluations:
            by_biz.setdefault(e.business_type, []).append(e)

        biz_summary = {}
        for biz, evs in by_biz.items():
            biz_summary[biz] = {
                "avg_similarity": round(
                    sum(e.avg_similarity.overall_similarity for e in evs) / len(evs), 1
                ),
                "avg_layout_score": round(
                    sum((e.layout_score or 0) for e in evs) / len(evs), 1
                ),
                "avg_final_score": round(
                    sum(e.final_score for e in evs) / len(evs), 1
                ),
                "count": len(evs),
            }

        return EvaluationReport(
            total_evaluations=len(evaluations),
            avg_final_score=round(avg_final, 1),
            avg_similarity=round(avg_sim, 1),
            avg_layout_score=round(avg_layout, 1),
            grade_distribution=grade_dist,
            evaluations=evaluations,
            by_business_type=biz_summary,
        )

    def _compare_with_case(
        self,
        gen_result: GenerationResult,
        real_case: dict,
    ) -> CaseComparison:
        """생성 결과와 실 사례 비교"""
        basic = real_case.get("basic_info", {})
        real_equipment = real_case.get("equipment_list", [])
        real_zones = real_case.get("zones", [])

        # 1. 카테고리 분포 유사도
        gen_cat_dist = category_distribution_from_generated(
            gen_result.generated_equipment
        )
        real_cat_dist = category_distribution_from_equipment(real_equipment)
        cat_sim = cosine_similarity(gen_cat_dist, real_cat_dist)

        # 2. 장비명 겹침 (Jaccard)
        gen_names = equipment_names_from_generated(gen_result.generated_equipment)
        real_names = equipment_names_from_real(real_equipment)
        name_overlap = jaccard_similarity(gen_names, real_names)

        # 3. 장비 수 정확도
        gen_count = len(gen_result.generated_equipment)
        real_count = len(real_equipment)
        count_acc = count_accuracy(gen_count, real_count)

        # 4. 구역 비율 유사도
        real_zone_dist = zone_ratio_from_zones(real_zones)
        zone_sim = cosine_similarity(
            gen_result.recommended_zone_ratios,
            real_zone_dist,
        ) if real_zone_dist else 0.5  # 구역 데이터 없으면 기본값

        # 종합 유사도
        overall = (
            cat_sim * SIMILARITY_WEIGHTS["equipment_category"]
            + name_overlap * SIMILARITY_WEIGHTS["equipment_name"]
            + count_acc * SIMILARITY_WEIGHTS["equipment_count"]
            + zone_sim * SIMILARITY_WEIGHTS["zone_ratio"]
        ) * 100

        metrics = SimilarityMetrics(
            equipment_category_similarity=round(cat_sim, 3),
            equipment_name_overlap=round(name_overlap, 3),
            equipment_count_accuracy=round(count_acc, 3),
            zone_ratio_similarity=round(zone_sim, 3),
            overall_similarity=round(overall, 1),
        )

        # 매칭/미싱/추가 장비
        matched = sorted(gen_names & real_names)
        missing = sorted(real_names - gen_names)
        extra = sorted(gen_names - real_names)

        return CaseComparison(
            case_number=basic.get("case_number", 0),
            business_type=basic.get("business_type_category", "unknown"),
            kitchen_area_py=basic.get("kitchen_area_py"),
            similarity_metrics=metrics,
            matched_equipment=matched,
            missing_equipment=missing,
            extra_equipment=extra,
        )

    def _average_metrics(
        self, comparisons: List[CaseComparison]
    ) -> SimilarityMetrics:
        """비교 결과들의 평균 지표"""
        if not comparisons:
            return SimilarityMetrics(
                equipment_category_similarity=0,
                equipment_name_overlap=0,
                equipment_count_accuracy=0,
                zone_ratio_similarity=0,
                overall_similarity=0,
            )

        n = len(comparisons)
        return SimilarityMetrics(
            equipment_category_similarity=round(
                sum(c.similarity_metrics.equipment_category_similarity for c in comparisons) / n, 3
            ),
            equipment_name_overlap=round(
                sum(c.similarity_metrics.equipment_name_overlap for c in comparisons) / n, 3
            ),
            equipment_count_accuracy=round(
                sum(c.similarity_metrics.equipment_count_accuracy for c in comparisons) / n, 3
            ),
            zone_ratio_similarity=round(
                sum(c.similarity_metrics.zone_ratio_similarity for c in comparisons) / n, 3
            ),
            overall_similarity=round(
                sum(c.similarity_metrics.overall_similarity for c in comparisons) / n, 1
            ),
        )
