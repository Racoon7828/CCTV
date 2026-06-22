# Changelog

## [Unreleased] - 2026-06-22

### Refactor

- **데이터 소스 통합**: `crime(2015-2024).xlsx`(CRIME_NEW_FILE) 제거
  - `build_crime_yearly()`를 `load_crime_csv()` 기반으로 전환
  - CSV의 `{연도}.{offset}` 컬럼에서 범죄유형별 건수를 직접 추출

- **CCTV 파일 중복 읽기 제거**: `load_cctv_new()`가 `CCTV_FILE`을 재읽는 대신
  `load_cctv()` 캐시를 재사용하여 자치구 합산으로 연도별 누적 수 산출

- **공통 상수 일원화**: `CRIME_TYPES` / `CRIME_OFFSETS`를 모듈 레벨 상수로 분리
  - 기존: `build_crime_yearly()`, `build_crime_trend()` 내부에 각각 선언
  - 이후: 파일 상단에 한 곳에서만 정의

- **헬퍼 함수 추출**: `_get_total_row(crime_raw)` 추가
  - 기존: 두 함수에 동일한 `row_sum` 추출 로직이 중복 작성
  - 이후: 공통 헬퍼로 추출하여 재사용

- **루프 최적화**: `build_crime_trend()`의 `row_sum` 계산을 루프 밖으로 이동
  - 기존: 연도 루프(10회)마다 동일한 필터링 연산 반복
  - 이후: 루프 진입 전 1회만 실행
