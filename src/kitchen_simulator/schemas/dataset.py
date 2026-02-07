"""데이터셋 스키마 정의 - 422개 주방 도면 이미지에서 추출되는 정형 데이터"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum


class BusinessTypeCategory(str, Enum):
    """표준화된 업종 카테고리"""
    KOREAN = "korean"  # 한식
    WESTERN = "western"  # 양식
    CHINESE = "chinese"  # 중식
    JAPANESE = "japanese"  # 일식
    CAFE = "cafe"  # 카페/커피전문점
    BAKERY = "bakery"  # 제과점
    FAST_FOOD = "fast_food"  # 패스트푸드
    CAFETERIA = "cafeteria"  # 구내식당
    SNACK_BAR = "snack_bar"  # 분식
    FRANCHISE = "franchise"  # 프랜차이즈
    OTHER = "other"  # 기타


class EquipmentCategory(str, Enum):
    """표준화된 장비 카테고리"""
    SERVING = "serving"  # 배식기기
    DISHWASHING = "dishwashing"  # 퇴식기기
    STORAGE = "storage"  # 저장기기
    PREP = "prep"  # 작업기기
    COOKING = "cooking"  # 조리기기
    REFRIGERATION = "refrigeration"  # 냉장/냉동
    VENTILATION = "ventilation"  # 환기/후드
    OTHER = "other"  # 기타


class KitchenShapeType(str, Enum):
    """주방 형태 유형"""
    RECTANGLE = "rectangle"  # 직사각형
    L_SHAPED = "L"  # ㄱ자형
    U_SHAPED = "U"  # ㄴ자형
    SQUARE_SHAPED = "square"  # ㅁ자형
    IRREGULAR = "irregular"  # 불규칙


class EquipmentItem(BaseModel):
    """장비 항목"""
    sequence: Optional[str] = Field(default=None, description="순번 (숫자 또는 코드)")
    name: str = Field(default="(unknown)", description="품목명 (예: 호떡구이기, 냉동.냉장고)")
    width_mm: Optional[float] = Field(default=None, description="가로(mm)")
    depth_mm: Optional[float] = Field(default=None, description="세로(mm)")
    height_mm: Optional[float] = Field(default=None, description="높이(mm)")
    quantity: int = Field(default=1, ge=1, description="수량")
    category: Optional[EquipmentCategory] = Field(default=None, description="표준 카테고리")
    remarks: Optional[str] = Field(default=None, description="비고")

    @field_validator("sequence", mode="before")
    @classmethod
    def coerce_sequence(cls, v):
        if v is None:
            return None
        return str(v)

    @field_validator("name", mode="before")
    @classmethod
    def default_name(cls, v):
        if v is None:
            return "(unknown)"
        return str(v)

    @field_validator("quantity", mode="before")
    @classmethod
    def default_quantity(cls, v):
        if v is None:
            return 1
        return v

    @field_validator("width_mm", "depth_mm", "height_mm", mode="before")
    @classmethod
    def clean_dimensions(cls, v):
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        # Try to parse string as number
        try:
            return float(v)
        except (ValueError, TypeError):
            return None  # "Door type" etc → None


class ZoneInfo(BaseModel):
    """동선 구역 정보"""
    zone_name: str = Field(default="(unknown)", description="구역명 (예: 조리구역, 배식구역)")
    equipment_items: List[str] = Field(default_factory=list, description="해당 장비 목록")

    @field_validator("zone_name", mode="before")
    @classmethod
    def default_zone_name(cls, v):
        if v is None:
            return "(unknown)"
        return str(v)

    @field_validator("equipment_items", mode="before")
    @classmethod
    def default_equipment_items(cls, v):
        if v is None:
            return []
        return v


class KitchenDimensions(BaseModel):
    """주방 치수"""
    total_width_mm: Optional[float] = Field(default=None, description="전체 가로(mm)")
    total_depth_mm: Optional[float] = Field(default=None, description="전체 세로(mm)")
    shape_type: Optional[KitchenShapeType] = Field(default=None, description="주방 형태")

    # ㄱ자, ㄴ자 등의 경우 추가 치수
    additional_dimensions: Optional[dict] = Field(default=None, description="추가 치수 정보")


class BasicInfo(BaseModel):
    """기본 정보"""
    business_type_raw: Optional[str] = Field(default=None, description="원문 업종 (예: 호떡 및 커피전문점)")
    business_type_category: Optional[BusinessTypeCategory] = Field(default=None, description="표준화된 업종 카테고리")
    menu: Optional[str] = Field(default=None, description="메뉴 (예: 호떡 外)")
    total_area_py: Optional[float] = Field(default=None, description="전체 평수(PY)")
    kitchen_area_py: Optional[float] = Field(default=None, description="주방 평수(PY)")
    table_count: Optional[int] = Field(default=None, ge=0, description="테이블 수")
    seat_count: Optional[int] = Field(default=None, ge=0, description="좌석 수")

    @field_validator("table_count", "seat_count", mode="before")
    @classmethod
    def clean_counts(cls, v):
        if v is None:
            return None
        if isinstance(v, int):
            return v
        # "1인-3EA/2인-1EA/4인-14EA" 같은 복합 문자열 → None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None


class EquipmentByCategory(BaseModel):
    """용도별 기기 분류"""
    serving_equipment: List[str] = Field(default_factory=list, description="배식기기 목록")
    dishwashing_equipment: List[str] = Field(default_factory=list, description="퇴식기기 목록")
    storage_equipment: List[str] = Field(default_factory=list, description="저장기기 목록")
    prep_equipment: List[str] = Field(default_factory=list, description="작업기기 목록")
    cooking_equipment: List[str] = Field(default_factory=list, description="조리기기 목록")

    @field_validator("serving_equipment", "dishwashing_equipment", "storage_equipment", "prep_equipment", "cooking_equipment", mode="before")
    @classmethod
    def default_equipment_list(cls, v):
        if v is None:
            return []
        return v


class ExtractionMetadata(BaseModel):
    """추출 메타데이터"""
    source_folder: Optional[str] = Field(default=None, description="원본 폴더명")
    case_id: Optional[str] = Field(default=None, description="케이스 ID (폴더명의 번호)")
    extracted_at: datetime = Field(default_factory=datetime.now, description="추출 일시")
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="추출 신뢰도 (0~1)")
    extractor_version: Optional[str] = Field(default=None, description="추출기 버전")
    notes: Optional[str] = Field(default=None, description="추가 노트")


class KitchenDataset(BaseModel):
    """주방 도면 데이터셋 전체 스키마"""

    # 기본 정보
    basic_info: BasicInfo = Field(description="기본 정보")

    # 장비 목록 (테이블 형태)
    equipment_list: List[EquipmentItem] = Field(default_factory=list, description="장비 목록")

    # 용도별 기기 분류
    equipment_by_category: Optional[EquipmentByCategory] = Field(default=None, description="용도별 기기 분류")

    # 주방 치수
    kitchen_dimensions: Optional[KitchenDimensions] = Field(default=None, description="주방 치수")

    # 동선 구역
    zones: List[ZoneInfo] = Field(default_factory=list, description="동선 구역 정보")

    # 설계 포인트
    design_points: List[str] = Field(default_factory=list, description="설계 포인트 (텍스트 리스트)")

    # 메타데이터
    metadata: ExtractionMetadata = Field(default_factory=ExtractionMetadata, description="추출 메타데이터")

    # 원본 이미지 경로 (선택)
    image_paths: List[str] = Field(default_factory=list, description="원본 이미지 파일 경로")

    class Config:
        json_schema_extra = {
            "example": {
                "basic_info": {
                    "business_type_raw": "호떡 및 커피전문점",
                    "business_type_category": "cafe",
                    "menu": "호떡 外",
                    "total_area_py": 8.16,
                    "kitchen_area_py": 3.0,
                    "table_count": 5,
                    "seat_count": 20
                },
                "equipment_list": [
                    {
                        "sequence": 1,
                        "name": "호떡구이기",
                        "width_mm": 600,
                        "depth_mm": 800,
                        "height_mm": 850,
                        "quantity": 1,
                        "category": "cooking"
                    },
                    {
                        "sequence": 2,
                        "name": "냉동.냉장고",
                        "width_mm": 900,
                        "depth_mm": 700,
                        "height_mm": 1900,
                        "quantity": 1,
                        "category": "refrigeration"
                    }
                ],
                "kitchen_dimensions": {
                    "total_width_mm": 4500,
                    "total_depth_mm": 3000,
                    "shape_type": "rectangle"
                },
                "zones": [
                    {
                        "zone_name": "조리구역",
                        "equipment_items": ["호떡구이기", "가스1구렌지"]
                    },
                    {
                        "zone_name": "저장구역",
                        "equipment_items": ["냉동.냉장고"]
                    }
                ],
                "design_points": [
                    "효율적인 동선 설계",
                    "좁은 공간 최적화"
                ],
                "metadata": {
                    "source_folder": "001_호떡전문점",
                    "case_id": "001",
                    "confidence_score": 0.92
                }
            }
        }
