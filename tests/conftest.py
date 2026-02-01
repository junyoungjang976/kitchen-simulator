"""pytest 설정"""
import sys
from pathlib import Path

# src 경로 추가
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))
