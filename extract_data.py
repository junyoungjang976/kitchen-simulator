"""주방 도면 이미지에서 정형 데이터 자동 추출 파이프라인

422개 주방 도면 이미지를 배치 처리하여 AI 비전(Google Gemini)으로 정형 데이터를 추출합니다.
"""

import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import PIL.Image
import google.generativeai as genai
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

# 스키마 import
from kitchen_simulator.schemas.dataset import (
    KitchenDataset,
    BasicInfo,
    EquipmentItem,
    EquipmentByCategory,
    KitchenDimensions,
    ZoneInfo,
    ExtractionMetadata,
    BusinessTypeCategory,
    EquipmentCategory,
    KitchenShapeType,
)

# 설정
SOURCE_DIR = Path("C:/Users/jangj/ai-ideation-lab/projects/kitchen-layout-simulator/도면 400종 (이미지 일체 미사용, 저작권 주의, 패턴만 참고)")
OUTPUT_DIR = Path("C:/Users/jangj/kitchen-simulator/data/extracted")
CASES_DIR = OUTPUT_DIR / "cases"
ERROR_LOG = OUTPUT_DIR / "errors.log"
DATASET_FILE = OUTPUT_DIR / "dataset.json"
MODEL_NAME = "gemini-2.0-flash"
EXTRACTOR_VERSION = "1.1.0-gemini"

# CLI 앱
app = typer.Typer()
console = Console()

# 출력 폴더 생성 (로거 설정 전)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(ERROR_LOG, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def get_case_folders() -> List[Path]:
    """소스 폴더에서 모든 케이스 폴더 목록 반환"""
    if not SOURCE_DIR.exists():
        console.print(f"[red]소스 폴더가 존재하지 않습니다: {SOURCE_DIR}[/red]")
        return []

    folders = [f for f in SOURCE_DIR.iterdir() if f.is_dir()]
    folders.sort()
    return folders


def extract_case_id(folder_name: str) -> str:
    """폴더명에서 케이스 ID 추출 (예: 137_퓨전_양식... -> 137)"""
    match = re.match(r"^(\d+)_", folder_name)
    return match.group(1) if match else folder_name


def find_target_image(folder: Path) -> Optional[Path]:
    """
    폴더에서 추출할 타겟 이미지 찾기
    우선순위: o_*.jpg > *2.jpg (동선도면) > *1.jpg (평면도)
    """
    images = list(folder.glob("*.jpg")) + list(folder.glob("*.JPG"))

    # 1순위: o_ 접두사 (종합 요약시트)
    o_images = [img for img in images if img.name.lower().startswith("o_")]
    if o_images:
        return o_images[0]

    # 2순위: 숫자2.jpg (동선도면)
    num2_images = [img for img in images if re.search(r"\d+2\.jpe?g$", img.name, re.IGNORECASE)]
    if num2_images:
        return num2_images[0]

    # 3순위: 숫자1.jpg (평면도)
    num1_images = [img for img in images if re.search(r"\d+1\.jpe?g$", img.name, re.IGNORECASE)]
    if num1_images:
        return num1_images[0]

    # 그 외: 첫 번째 이미지
    return images[0] if images else None


def load_image_for_gemini(image_path: Path) -> PIL.Image.Image:
    """이미지 파일을 Gemini용으로 로드"""
    return PIL.Image.open(image_path)


def get_extraction_prompt() -> str:
    """Claude에게 전달할 데이터 추출 프롬프트"""
    return """당신은 한국어 주방 도면 이미지에서 정형 데이터를 추출하는 전문가입니다.

주어진 이미지에서 다음 정보를 추출하여 JSON 형식으로 반환하세요.

## 추출할 정보

### 1. 기본 정보 (basic_info)
- business_type_raw: 업종 원문 (예: "호떡 및 커피전문점", "한식당", "구내식당")
- business_type_category: 표준 카테고리 매핑
  - 한식, 한정식 → "korean"
  - 양식 → "western"
  - 중식 → "chinese"
  - 일식, 일식당 → "japanese"
  - 카페, 커피전문점 → "cafe"
  - 제과점, 베이커리 → "bakery"
  - 패스트푸드 → "fast_food"
  - 구내식당 → "cafeteria"
  - 분식 → "snack_bar"
  - 프랜차이즈 → "franchise"
  - 기타 → "other"
- menu: 메뉴 (예: "호떡 外", "삼겹살, 된장찌개")
- total_area_py: 전체 평수 (PY 단위)
- kitchen_area_py: 주방 평수 (PY 단위)
- table_count: 테이블 수
- seat_count: 좌석 수

### 2. 장비 목록 (equipment_list)
각 장비에 대해:
- sequence: 순번
- name: 품목명 (예: "호떡구이기", "냉동.냉장고", "작업대")
- width_mm: 가로(mm)
- depth_mm: 세로(mm)
- height_mm: 높이(mm)
- quantity: 수량
- category: 장비 카테고리
  - 배식기기 → "serving"
  - 퇴식기기, 식기세척기 → "dishwashing"
  - 저장, 선반, 진열대 → "storage"
  - 작업대, 조리대 → "prep"
  - 가스렌지, 그릴, 튀김기, 오븐 → "cooking"
  - 냉장고, 냉동고 → "refrigeration"
  - 후드, 환기 → "ventilation"
  - 기타 → "other"
- remarks: 비고

### 3. 용도별 기기 분류 (equipment_by_category) - 선택사항
- serving_equipment: 배식기기 목록 (문자열 배열)
- dishwashing_equipment: 퇴식기기 목록
- storage_equipment: 저장기기 목록
- prep_equipment: 작업기기 목록
- cooking_equipment: 조리기기 목록

### 4. 주방 치수 (kitchen_dimensions)
- total_width_mm: 전체 가로(mm)
- total_depth_mm: 전체 세로(mm)
- shape_type: 주방 형태
  - 직사각형 → "rectangle"
  - ㄱ자형 → "L"
  - ㄴ자형 → "U"
  - ㅁ자형 → "square"
  - 불규칙 → "irregular"

### 5. 동선 구역 (zones)
각 구역에 대해:
- zone_name: 구역명 (예: "조리구역", "배식구역", "저장구역")
- equipment_items: 해당 구역 장비 목록 (문자열 배열)

### 6. 설계 포인트 (design_points)
이미지에서 언급된 설계 특징이나 포인트를 문자열 배열로 (예: ["효율적인 동선 설계", "좁은 공간 최적화"])

## 출력 형식

반드시 다음 JSON 스키마를 준수하세요:

```json
{
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
      "category": "cooking",
      "remarks": null
    }
  ],
  "equipment_by_category": {
    "serving_equipment": [],
    "dishwashing_equipment": ["식기세척기"],
    "storage_equipment": ["선반"],
    "prep_equipment": ["작업대"],
    "cooking_equipment": ["호떡구이기", "가스렌지"]
  },
  "kitchen_dimensions": {
    "total_width_mm": 4500,
    "total_depth_mm": 3000,
    "shape_type": "rectangle",
    "additional_dimensions": null
  },
  "zones": [
    {
      "zone_name": "조리구역",
      "equipment_items": ["호떡구이기", "가스렌지"]
    }
  ],
  "design_points": [
    "효율적인 동선 설계",
    "좁은 공간 최적화"
  ]
}
```

## 중요 규칙
1. 이미지에서 명확히 읽을 수 없는 항목은 null로 반환하세요.
2. 숫자는 반드시 숫자 타입으로 (문자열 아님).
3. 카테고리는 반드시 지정된 영어 값 중 하나를 사용하세요.
4. JSON 외 다른 텍스트는 포함하지 마세요.
5. 코드 블록(```json)으로 감싸서 반환하세요.

지금 이미지를 분석하여 JSON을 추출해주세요."""


def parse_json_from_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Claude 응답에서 JSON 추출
    - ```json ... ``` 블록에서 추출 시도
    - 실패 시 전체 텍스트에서 {} 패턴 추출
    """
    # 1. 코드 블록에서 추출
    match = re.search(r"```json\s*\n(.*?)\n```", response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as e:
            logger.warning(f"코드 블록 JSON 파싱 실패: {e}")

    # 2. 전체 텍스트에서 {} 추출
    match = re.search(r"\{.*\}", response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as e:
            logger.warning(f"전체 텍스트 JSON 파싱 실패: {e}")

    return None


def extract_from_image(
    model: genai.GenerativeModel,
    image_path: Path,
    case_id: str,
    folder_name: str,
    max_retries: int = 3
) -> Optional[KitchenDataset]:
    """이미지에서 데이터 추출 (429 재시도 포함)"""

    for attempt in range(max_retries + 1):
        try:
            # 이미지 로드
            img = load_image_for_gemini(image_path)

            # API 호출
            response = model.generate_content([get_extraction_prompt(), img])

            # 응답 텍스트 추출
            response_text = response.text

            # JSON 파싱
            extracted_data = parse_json_from_response(response_text)
            if not extracted_data:
                logger.error(f"[{case_id}] JSON 파싱 실패")
                return None

            # 메타데이터 추가
            extracted_data["metadata"] = {
                "source_folder": folder_name,
                "case_id": case_id,
                "extracted_at": datetime.now().isoformat(),
                "extractor_version": EXTRACTOR_VERSION,
            }

            # 이미지 경로 추가
            extracted_data["image_paths"] = [str(image_path)]

            # Pydantic 검증
            dataset = KitchenDataset(**extracted_data)
            return dataset

        except Exception as e:
            error_str = str(e)
            # 429 Rate limit → retry with exponential backoff
            if "429" in error_str or "ResourceExhausted" in error_str:
                if attempt < max_retries:
                    wait_time = 30 * (2 ** attempt)  # 30s, 60s, 120s
                    logger.warning(f"[{case_id}] Rate limit (429). {wait_time}초 대기 후 재시도 ({attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

            logger.error(f"[{case_id}] 추출 실패: {e}", exc_info=True)
            return None

    return None


def save_case_json(case_id: str, dataset: KitchenDataset) -> None:
    """케이스별 JSON 저장"""
    output_file = CASES_DIR / f"{case_id}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dataset.model_dump(), f, ensure_ascii=False, indent=2, default=str)


def load_case_json(case_id: str) -> Optional[KitchenDataset]:
    """저장된 케이스 JSON 로드"""
    output_file = CASES_DIR / f"{case_id}.json"
    if not output_file.exists():
        return None

    try:
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return KitchenDataset(**data)
    except Exception as e:
        logger.warning(f"[{case_id}] JSON 로드 실패: {e}")
        return None


@app.command()
def run(
    start: int = typer.Option(None, help="시작 인덱스 (0부터)"),
    end: int = typer.Option(None, help="종료 인덱스 (포함)"),
    force: bool = typer.Option(False, help="기존 결과 덮어쓰기"),
    delay: float = typer.Option(8.0, help="요청 간 대기 시간(초)"),
):
    """배치 추출 실행"""

    # API 키 확인 (환경변수 우선, 없으면 하드코딩 폴백)
    api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyCPHWrdrzuyvnzwxe6AemYA4Y86PfLPC_k")
    if not api_key:
        console.print("[red]환경변수 GEMINI_API_KEY가 설정되지 않았습니다.[/red]")
        raise typer.Exit(1)

    # 출력 폴더 생성
    CASES_DIR.mkdir(parents=True, exist_ok=True)

    # Gemini 설정 및 모델 생성
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)

    # 케이스 폴더 목록
    folders = get_case_folders()
    if not folders:
        console.print("[red]처리할 케이스가 없습니다.[/red]")
        raise typer.Exit(1)

    # 범위 설정
    if start is not None:
        folders = folders[start:]
    if end is not None:
        folders = folders[: end - (start or 0) + 1]

    console.print(f"[cyan]총 {len(folders)}개 케이스 처리 시작[/cyan]")

    # 진행률 표시
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[green]추출 중...", total=len(folders))

        success_count = 0
        skip_count = 0
        error_count = 0

        for folder in folders:
            case_id = extract_case_id(folder.name)
            progress.update(task, description=f"[green]추출 중: {case_id}")

            # 기존 결과 확인
            if not force and load_case_json(case_id):
                logger.info(f"[{case_id}] 이미 추출됨 (스킵)")
                skip_count += 1
                progress.advance(task)
                continue

            # 타겟 이미지 찾기
            image_path = find_target_image(folder)
            if not image_path:
                logger.error(f"[{case_id}] 이미지를 찾을 수 없음: {folder}")
                error_count += 1
                progress.advance(task)
                continue

            # 추출 실행
            logger.info(f"[{case_id}] 추출 시작: {image_path.name}")
            dataset = extract_from_image(model, image_path, case_id, folder.name)

            if dataset:
                save_case_json(case_id, dataset)
                logger.info(f"[{case_id}] 추출 성공")
                success_count += 1
            else:
                logger.error(f"[{case_id}] 추출 실패")
                error_count += 1

            progress.advance(task)

            # Rate limiting
            if delay > 0:
                time.sleep(delay)

    # 결과 요약
    console.print("\n[bold green]추출 완료[/bold green]")
    console.print(f"  성공: {success_count}")
    console.print(f"  스킵: {skip_count}")
    console.print(f"  실패: {error_count}")


@app.command()
def status():
    """추출 현황 확인"""
    folders = get_case_folders()
    if not folders:
        console.print("[red]소스 폴더가 비어있습니다.[/red]")
        return

    total = len(folders)
    completed = 0
    failed = 0

    for folder in folders:
        case_id = extract_case_id(folder.name)
        if load_case_json(case_id):
            completed += 1

    # 에러 로그 확인
    if ERROR_LOG.exists():
        with open(ERROR_LOG, "r", encoding="utf-8") as f:
            failed = len([line for line in f if "추출 실패" in line])

    remaining = total - completed

    # 테이블 출력
    table = Table(title="추출 현황")
    table.add_column("항목", style="cyan")
    table.add_column("건수", justify="right", style="magenta")

    table.add_row("전체", str(total))
    table.add_row("완료", str(completed), style="green")
    table.add_row("실패", str(failed), style="red")
    table.add_row("남은 건수", str(remaining), style="yellow")

    console.print(table)


@app.command()
def merge():
    """개별 JSON을 dataset.json으로 병합"""
    if not CASES_DIR.exists():
        console.print("[red]추출된 케이스가 없습니다.[/red]")
        raise typer.Exit(1)

    case_files = sorted(CASES_DIR.glob("*.json"))
    if not case_files:
        console.print("[red]병합할 케이스가 없습니다.[/red]")
        raise typer.Exit(1)

    datasets = []
    for case_file in case_files:
        try:
            with open(case_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            datasets.append(data)
        except Exception as e:
            logger.warning(f"{case_file.name} 로드 실패: {e}")

    # 전체 데이터셋 저장
    output_data = {
        "version": EXTRACTOR_VERSION,
        "total_cases": len(datasets),
        "created_at": datetime.now().isoformat(),
        "cases": datasets,
    }

    with open(DATASET_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2, default=str)

    console.print(f"[green]병합 완료: {len(datasets)}개 케이스 → {DATASET_FILE}[/green]")


if __name__ == "__main__":
    app()
