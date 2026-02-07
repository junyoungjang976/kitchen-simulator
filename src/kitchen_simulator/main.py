"""식당 주방 설계 시뮬레이터 CLI"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .domain.kitchen import Kitchen, KitchenShape, RestaurantType
from .domain.zone import ZoneType
from .schemas.input import KitchenInput
from .schemas.output import (
    SimulationOutput, ZoneOutput, PlacementOutput,
    ValidationResult, ScoreMetrics
)
from .engine.zone_engine import ZoneEngine
from .engine.placement_engine import PlacementEngine
from .engine.validation_engine import ValidationEngine
from .engine.scoring_engine import ScoringEngine
from .engine.optimizer import Optimizer
from .geometry.polygon import create_polygon, create_rectangle, get_vertices
from .data.equipment_catalog import EQUIPMENT_CATALOG, get_equipment_for_restaurant

app = typer.Typer(help="식당 주방 설계 시뮬레이터")
console = Console()

@app.command()
def simulate(
    input_file: Optional[Path] = typer.Argument(None, help="입력 JSON 파일"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="출력 JSON 파일"),
    restaurant_type: str = typer.Option("casual", "--type", "-t", help="식당 유형"),
    seats: int = typer.Option(50, "--seats", "-s", help="좌석 수"),
    width: float = typer.Option(0, "--width", "-w", help="주방 가로 (m)"),
    depth: float = typer.Option(0, "--depth", "-d", help="주방 세로 (m)"),
    iterations: int = typer.Option(100, "--iterations", "-i", help="최적화 반복 횟수"),
    seed: Optional[int] = typer.Option(None, "--seed", help="랜덤 시드"),
):
    """주방 레이아웃 시뮬레이션 실행"""

    # 입력 파일이 있으면 로드
    if input_file and input_file.exists():
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        kitchen_input = KitchenInput.model_validate(data)
    else:
        # CLI 옵션으로 입력 생성
        area = seats * 0.46 if width == 0 else width * depth
        if width == 0:
            # 정사각형에 가깝게 자동 계산
            width = (area ** 0.5) * 1.2
            depth = area / width

        kitchen_input = KitchenInput(
            restaurant_type=restaurant_type,
            seat_count=seats,
            total_area_sqm=width * depth,
            width=width,
            depth=depth,
        )

    console.print(Panel(f"[bold blue]주방 시뮬레이션 시작[/bold blue]\n"
                        f"유형: {kitchen_input.restaurant_type}\n"
                        f"좌석: {kitchen_input.seat_count}\n"
                        f"면적: {kitchen_input.get_area():.1f}㎡"))

    # Kitchen 객체 생성
    if kitchen_input.vertices:
        vertices = kitchen_input.vertices
        shape = KitchenShape(kitchen_input.shape.value)
    else:
        vertices = [
            (0, 0),
            (kitchen_input.width, 0),
            (kitchen_input.width, kitchen_input.depth),
            (0, kitchen_input.depth),
        ]
        shape = KitchenShape.RECTANGLE

    kitchen = Kitchen(
        shape=shape,
        vertices=vertices,
        restaurant_type=RestaurantType(kitchen_input.restaurant_type.value),
        seat_count=kitchen_input.seat_count,
    )

    # 최적화 실행
    with console.status("[bold green]최적화 중..."):
        optimizer = Optimizer(seed=seed)
        result = optimizer.optimize(
            kitchen,
            iterations=iterations,
            fixed_elements=kitchen_input.fixed_elements,
        )

    # 결과 출력
    _print_result(result, kitchen)

    # JSON 출력
    output = _create_output(result, kitchen_input, kitchen)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output.model_dump_json(indent=2))
        console.print(f"\n[green]결과 저장됨: {output_file}[/green]")
    else:
        console.print("\n[dim]--output 옵션으로 JSON 파일 저장 가능[/dim]")

    return output

def _print_result(result, kitchen):
    """결과 테이블 출력"""
    # 점수 테이블
    score_table = Table(title="점수 분석", show_header=True)
    score_table.add_column("항목", style="cyan")
    score_table.add_column("점수", justify="right")

    score = result.best_score
    score_table.add_row("동선 효율", f"{score.workflow_efficiency*100:.1f}%")
    score_table.add_row("공간 활용", f"{score.space_utilization*100:.1f}%")
    score_table.add_row("안전 준수", f"{score.safety_compliance*100:.1f}%")
    score_table.add_row("접근성", f"{score.accessibility*100:.1f}%")
    score_table.add_row("[bold]종합 점수[/bold]", f"[bold]{score.overall:.1f}[/bold]")

    console.print(score_table)

    # 구역 테이블
    zone_table = Table(title="구역 배치", show_header=True)
    zone_table.add_column("구역", style="cyan")
    zone_table.add_column("면적", justify="right")
    zone_table.add_column("비율", justify="right")

    total_area = kitchen.area
    for zone in result.best_zones:
        ratio = zone.area / total_area * 100 if total_area > 0 else 0
        zone_table.add_row(
            zone.zone_type.value,
            f"{zone.area:.1f}㎡",
            f"{ratio:.1f}%"
        )

    console.print(zone_table)

    # 장비 배치 요약
    console.print(f"\n배치된 장비: {len(result.best_placements.placements)}개")
    if result.best_placements.unplaced:
        console.print(f"[yellow]미배치 장비: {len(result.best_placements.unplaced)}개[/yellow]")

    console.print(f"\n[dim]반복: {result.iterations_run}회, "
                  f"시간: {result.computation_time_ms:.0f}ms[/dim]")

def _create_output(result, kitchen_input, kitchen) -> SimulationOutput:
    """SimulationOutput 생성"""
    zones = [
        ZoneOutput(
            type=z.zone_type.value,
            polygon=z.polygon,
            area_sqm=round(z.area, 2),
            ratio=round(z.area / kitchen.area, 3) if kitchen.area > 0 else 0,
            equipment_ids=z.equipment_ids,
        )
        for z in result.best_zones
    ]

    placements = []
    for p in result.best_placements.placements:
        equip_id = p.equipment_id.rsplit("_", 1)[0]  # 인덱스 제거
        equip = EQUIPMENT_CATALOG.get(equip_id)
        if equip:
            placements.append(PlacementOutput(
                equipment_id=p.equipment_id,
                equipment_name=equip.name_ko,
                zone=p.zone_type.value,
                x=round(p.x, 2),
                y=round(p.y, 2),
                width=equip.width,
                depth=equip.depth,
                rotation=p.rotation,
            ))

    validation = ValidationResult(
        passed=result.best_score.safety_compliance >= 0.8,
        errors=[],
        warnings=result.best_placements.warnings,
    )

    scores = ScoreMetrics(
        workflow_efficiency=result.best_score.workflow_efficiency,
        space_utilization=result.best_score.space_utilization,
        safety_compliance=result.best_score.safety_compliance,
        accessibility=result.best_score.accessibility,
        overall=result.best_score.overall,
    )

    return SimulationOutput(
        success=True,
        simulation_id=str(uuid.uuid4())[:8],
        input_summary={
            "restaurant_type": kitchen_input.restaurant_type.value,
            "seat_count": kitchen_input.seat_count,
            "shape": kitchen_input.shape.value,
        },
        total_area_sqm=round(kitchen.area, 2),
        zones=zones,
        placements=placements,
        validation=validation,
        scores=scores,
        iterations_run=result.iterations_run,
        computation_time_ms=round(result.computation_time_ms, 1),
    )

@app.command()
def validate(input_file: Path):
    """입력 JSON 파일 유효성 검사"""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        kitchen_input = KitchenInput.model_validate(data)
        console.print("[green]유효한 입력 파일입니다[/green]")
        console.print(f"유형: {kitchen_input.restaurant_type}")
        console.print(f"좌석: {kitchen_input.seat_count}")
        console.print(f"면적: {kitchen_input.get_area():.1f}㎡")
    except Exception as e:
        console.print(f"[red]오류: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def equipment_list(restaurant_type: str = "casual"):
    """식당 유형별 기본 장비 목록 출력"""
    equipment = get_equipment_for_restaurant(restaurant_type)

    table = Table(title=f"{restaurant_type} 기본 장비", show_header=True)
    table.add_column("ID", style="dim")
    table.add_column("이름", style="cyan")
    table.add_column("크기 (가로×세로)", justify="right")
    table.add_column("구역")

    for eq in equipment:
        table.add_row(
            eq.id,
            eq.name_ko,
            f"{eq.width*100:.0f}×{eq.depth*100:.0f}cm",
            eq.category.value,
        )

    console.print(table)

if __name__ == "__main__":
    app()
