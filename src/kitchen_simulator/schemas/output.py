"""출력 스키마 정의"""
from pydantic import BaseModel, Field
from typing import List, Tuple, Optional
from datetime import datetime

class ZoneOutput(BaseModel):
    """구역 출력"""
    type: str
    polygon: List[Tuple[float, float]]
    area_sqm: float
    ratio: float  # 전체 대비 비율
    equipment_ids: List[str] = Field(default_factory=list)

class PlacementOutput(BaseModel):
    """장비 배치 출력"""
    equipment_id: str
    equipment_name: str
    zone: str
    x: float
    y: float
    width: float
    depth: float
    rotation: int = 0

class ValidationResult(BaseModel):
    """검증 결과"""
    passed: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class ScoreMetrics(BaseModel):
    """점수 지표"""
    workflow_efficiency: float = Field(ge=0, le=1)
    space_utilization: float = Field(ge=0, le=1)
    safety_compliance: float = Field(ge=0, le=1)
    accessibility: float = Field(ge=0, le=1)
    overall: float = Field(ge=0, le=100)

class SimulationOutput(BaseModel):
    """시뮬레이션 출력"""
    success: bool
    simulation_id: str
    timestamp: datetime = Field(default_factory=datetime.now)

    # 입력 요약
    input_summary: dict

    # 결과
    total_area_sqm: float
    zones: List[ZoneOutput]
    placements: List[PlacementOutput]

    # 검증 및 점수
    validation: ValidationResult
    scores: ScoreMetrics

    # 메타데이터
    iterations_run: int = 0
    computation_time_ms: float = 0

class SimulationError(BaseModel):
    """에러 응답"""
    success: bool = False
    error_code: str
    message: str
    details: Optional[dict] = None
