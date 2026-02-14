# busungtk-kitchen-simulator - 주방 시뮬레이터

업소용 주방 레이아웃 자동 생성 알고리즘 (CLI)

## 기술 스택
- **Language**: Python 3.11+
- **CLI**: Typer
- **Geometry**: Shapely
- **Validation**: Pydantic
- **Test**: pytest

## 프로젝트 구조
src/kitchen_simulator/
├── domain/        # 도메인 모델
├── engine/        # 배치 엔진
├── evaluation/    # 평가 시스템
├── generator/     # 레이아웃 생성기
├── geometry/      # 기하학 연산
├── patterns/      # 배치 패턴
├── schemas/       # 스키마
└── data/          # 데이터

## 주요 기능
- 주방 레이아웃 자동 생성 알고리즘
- 4-zone 파티셔닝 기반 설비 배치
- 공간 분석 (Shapely)
- 레이아웃 평가 및 점수화

## 명령어
- `pip install -e .` - 개발 설치
- `pip install -e ".[dev]"` - dev 의존성 포함 설치
- `pytest` - 테스트 실행

## 배포
- 로컬 CLI (웹 배포 없음)

---

## 부성티케이 프로젝트 생태계

| 레포 | 역할 | 스택 | 배포 |
|------|------|------|------|
| busungtk-equipment | 장비관리 포털 | React 19 + Vite + Supabase | Vercel |
| busungtk-asms | A/S 관리 시스템 | React 19 + Vite + Supabase | Vercel |
| busungtk-as-diagnosis | 설비 A/S 진단 도구 | Next.js 16 + Prisma + LibSQL | Vercel |
| busungtk-hub | 통합 운영 플랫폼 | Next.js 16 + Supabase SSR | Vercel |
| busungtk-portal | 업무 포털 | Static HTML | Vercel |
| busungtk-landing | B2B 랜딩페이지 | Static HTML | Vercel |
| busungtk-work-history | 작업 히스토리 | Static HTML + Chart.js | GitHub Pages |
| busungtk-daily-report | 일일 보고 | Next.js 16 + Supabase | Vercel |
| busungtk-order-tracker | 주문 추적 | React 19 + Vite + Google APIs | Vercel |
| busungtk-marketing | 마케팅 | Next.js 16 + Recharts | Vercel |
| busungtk-sales-crm | CRM | React 19 + Vite + Supabase | Vercel |
| busungtk-sales-pipeline | 영업 파이프라인 | React 19 + Vite + Vitest | Vercel |
| busungtk-field-check | 현장 점검 | React 19 + Vite + Kakao Maps + PWA | Vercel |
| busungtk-kitchen-planner | 주방 설계 | React 19 + Vite + Konva | Vercel |
| busungtk-kitchen-simulator | 주방 시뮬레이터 | Python + Typer + Shapely | CLI |
| busungtk-purchase-data | 매입 데이터 | Python 스크립트 | 로컬 |
| busungtk-hvac-mentor | HVAC 멘토 | React 19 + Vite + Gemini AI | Vercel |
| busungtk-ai-ideation | AI 아이디에이션 | Documentation | GitHub |
| busungtk-ai-trends | AI 트렌드 | Next.js 14 + OpenAI | Vercel |

## 공통 운영 규칙

### 최우선 원칙
1. 기존 기능/데이터를 깨뜨릴 가능성이 있으면 **즉시 중단하고 보고**
2. 보안/권한/RLS/시크릿 관련 작업은 **승인 없이 진행하지 않음**
3. 한 번에 크게 바꾸지 않음 (**작게, 자주, 검증하며**)
4. 결정 권한은 항상 사용자에게 있으며 Claude는 실행 담당

### 수정 금지 영역 (승인 필수)
- `.env`, `.env.*` (API 키, DB 키)
- Supabase RLS 정책
- DB 스키마 변경 (테이블/컬럼/인덱스/트리거)
- 마이그레이션 파일
- auth 관련 핵심 흐름

### 작업 규칙
- 한 작업 = 하나의 목적, 수정 파일 최대 3개
- DB/RLS 작업은 코드 작업과 분리
- "겸사겸사 개선" 금지
- 작업 후 변경 사항을 자연어로 설명

### Supabase 안전 규칙
- 대부분의 프로젝트가 동일 Supabase 인스턴스(`fgnkrhgbvohmxaetejyx`) 공유
- 스키마 변경 시 다른 프로젝트 영향도 반드시 확인
- SQL 실행 시 왜 필요한지 쉽게 설명

### Git 규칙
- 커밋 메시지 접두사: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- 배포/push/commit은 사용자가 "작업 끝났다"라고 말할 때 진행
