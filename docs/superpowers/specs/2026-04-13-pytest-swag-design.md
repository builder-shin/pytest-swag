# pytest-swag Design Spec

## Overview

pytest-swag은 pytest 테스트 코드에서 OpenAPI(Swagger) 문서를 자동 생성하는 pytest 플러그인이다. Ruby의 rswag에서 영감을 받았으며, 테스트 실행과 동시에 API 응답을 스키마로 검증하고, 검증을 통과한 테스트의 스펙만 OpenAPI 문서에 포함한다.

## 핵심 원칙

- **프레임워크 비의존**: 특정 HTTP 클라이언트나 웹 프레임워크에 종속되지 않는다
- **테스트-문서 동기화**: 응답 스키마 검증은 필수이며, 테스트가 통과해야만 문서에 반영된다
- **Pythonic DSL**: pytest fixture 기반 빌더 패턴으로 API 스펙을 정의한다
- **최소 의존성**: 코어는 pytest + jsonschema만 필요하다

## 타겟 사용자

프레임워크에 관계없이 pytest로 API 테스트를 작성하는 모든 Python 개발자.

## 패키지 구조

```
pytest-swag/
├── src/
│   └── pytest_swag/
│       ├── __init__.py          # 공개 API export
│       ├── plugin.py            # pytest 플러그인 등록 (fixture, hook)
│       ├── builder.py           # Swag DSL 빌더 (핵심 객체)
│       ├── collector.py         # 테스트 실행 중 스펙 데이터 수집
│       ├── generator.py         # 수집된 데이터 → OpenAPI JSON/YAML 변환
│       ├── validator.py         # 응답 스키마 검증
│       ├── schema.py            # OpenAPI 3.0/3.1 스키마 모델 정의
│       └── config.py            # 설정 관리 (conftest.py 또는 pyproject.toml)
├── tests/
│   ├── unit/
│   │   ├── test_builder.py
│   │   ├── test_validator.py
│   │   ├── test_collector.py
│   │   └── test_generator.py
│   ├── integration/
│   │   ├── test_plugin.py
│   │   └── test_full_flow.py
│   └── fixtures/
│       └── expected_outputs/
├── pyproject.toml
├── LICENSE                      # MIT
└── README.md
```

- `src` layout 사용 (PyPI 배포 표준)
- pytest 플러그인은 `entry_points`로 자동 등록 — `pip install pytest-swag`만 하면 바로 사용 가능
- 각 모듈은 단일 책임: builder는 DSL, collector는 수집, generator는 출력, validator는 검증

## 핵심 API — Swag Builder DSL

사용자가 직접 다루는 `swag` fixture의 인터페이스:

```python
def test_create_blog(swag):
    # 1) 경로 + HTTP 메서드 + 요약
    swag.path("/blogs").post("Creates a blog")

    # 2) 태그 (API 그룹핑)
    swag.tag("Blogs")

    # 3) 파라미터 정의
    swag.parameter("X-Api-Key", in_="header", schema={"type": "string"}, required=True)

    # 4) 요청 바디 정의
    swag.request_body(
        content_type="application/json",
        schema={
            "type": "object",
            "required": ["title"],
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
            }
        }
    )

    # 5) 응답 정의 (여러 상태 코드 가능)
    swag.response(201, description="Blog created", schema={
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "title": {"type": "string"},
        }
    })
    swag.response(422, description="Validation failed")

    # 6) 실제 테스트 실행 + 검증
    response = client.post("/blogs", json={"title": "Hello"})
    swag.validate(response.status_code, response.json())
```

### DSL 설계 포인트

- **`swag.path(path).method(summary)`**: 메서드 체이닝으로 경로와 HTTP 메서드를 한 줄에 정의
- **`swag.validate(status_code, body)`**: 상태 코드에 매칭되는 응답 스키마로 검증. 불일치 시 `pytest.fail()` 호출
- **`swag.validate()` 호출 필수**: 테스트에서 `swag.validate()`를 호출하지 않으면 해당 테스트의 스펙은 문서에 포함되지 않으며, `--swag-strict` 모드에서는 경고를 출력한다
- **다중 응답 테스트**: 하나의 테스트에서 하나의 상태 코드만 검증. 같은 엔드포인트의 다른 상태 코드는 별도 테스트로 분리
- **스키마는 plain dict**: 별도 스키마 DSL 없이 JSON Schema dict를 그대로 사용. 학습 비용 제로
- **`swag` fixture는 function scope**: 테스트마다 독립된 빌더 인스턴스가 생성된다. `swag_config`, `swag_schemas`, `swag_security_schemes`는 session scope

## 설정 및 OpenAPI 메타데이터

### conftest.py에서 fixture로 설정

```python
# conftest.py
import pytest

@pytest.fixture(scope="session")
def swag_config():
    return {
        "openapi": "3.1.0",          # 또는 "3.0.3"
        "info": {
            "title": "Blog API",
            "version": "1.0.0",
            "description": "A simple blog API",
        },
        "servers": [
            {"url": "https://api.example.com/v1"}
        ],
        "output_path": "docs/openapi.json",
        "output_format": "json",      # "json" | "yaml" | "both"
    }
```

### pyproject.toml에서 설정

```toml
[tool.pytest-swag]
openapi = "3.1.0"
output_path = "docs/openapi.json"
output_format = "both"

[tool.pytest-swag.info]
title = "Blog API"
version = "1.0.0"
```

### 설정 우선순위

`conftest.py`의 `swag_config` fixture > `pyproject.toml` > 기본값

### 다중 문서 지원

`swag_config`를 리스트로 반환하면 여러 OpenAPI 문서 생성 가능 (v1/v2 분리 등):

```python
@pytest.fixture(scope="session")
def swag_config():
    return [
        {"info": {"title": "Blog API v1", "version": "1.0.0"}, "output_path": "docs/v1.json"},
        {"info": {"title": "Blog API v2", "version": "2.0.0"}, "output_path": "docs/v2.json"},
    ]
```

다중 문서일 때 `swag.doc("Blog API v2")`로 어느 문서에 포함할지 지정. `info.title` 값으로 매칭한다. 미지정 시 첫 번째 문서에 포함.

## 스키마 검증과 테스트 흐름

### 검증 흐름

```
swag.validate(status_code, body)
    │
    ├─ 1) status_code가 swag.response()로 정의되었는지 확인
    │     └─ 미정의 → pytest.fail("Undocumented status code: 404")
    │
    ├─ 2) 해당 status_code에 schema가 정의되어 있으면 body를 JSON Schema로 검증
    │     └─ 불일치 → pytest.fail("Schema validation failed: ...")
    │
    └─ 3) 검증 통과 → 응답 데이터를 collector에 기록 (문서 생성용)
```

### 검증 라이브러리

`jsonschema` 사용:
- OpenAPI 3.0 → JSON Schema Draft 4 검증
- OpenAPI 3.1 → JSON Schema Draft 2020-12 검증

### 실패 메시지

```
E   SwagValidationError: Schema validation failed for POST /blogs → 201
E
E   Path: $.title
E   Expected: string
E   Got: integer (value: 42)
```

### $ref 지원 — 공유 스키마 재사용

```python
# conftest.py
@pytest.fixture(scope="session")
def swag_schemas():
    return {
        "Blog": {
            "type": "object",
            "required": ["id", "title"],
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string"},
            }
        }
    }

# test_blogs.py
def test_get_blog(swag):
    swag.path("/blogs/{id}").get("Retrieves a blog")
    swag.parameter("id", in_="path", schema={"type": "string"})
    swag.response(200, schema={"$ref": "#/components/schemas/Blog"})

    response = client.get("/blogs/1")
    swag.validate(response.status_code, response.json())
```

`swag_schemas` fixture로 정의한 스키마는 `components/schemas`에 자동 등록되고, `$ref`로 참조할 수 있다.

## 문서 생성 파이프라인

### 생성 시점: pytest session 종료 시

```
pytest 실행
    │
    ├─ 각 테스트 실행 → swag 빌더가 스펙 데이터를 collector에 기록
    │
    └─ pytest_sessionfinish hook
          │
          ├─ collector가 수집한 모든 스펙 데이터를 병합
          │     ├─ 같은 path + method → 응답 코드별로 합산
          │     └─ 충돌 감지 (같은 엔드포인트에 다른 스키마 정의 → 경고)
          │
          ├─ generator가 OpenAPI 문서 구조로 변환
          │     ├─ swag_config의 메타데이터 적용
          │     ├─ swag_schemas를 components/schemas에 삽입
          │     └─ paths, parameters, responses 정리
          │
          └─ 파일 출력
                ├─ JSON (json 모듈)
                └─ YAML (PyYAML)
```

### CLI 옵션

```bash
# 기본 — 테스트 실행 + 문서 생성
pytest --swag

# 문서 생성만 (출력 경로 오버라이드)
pytest --swag --swag-output=api-docs/openapi.yaml

# 문서 생성 건너뛰기 (swag fixture는 동작하되 파일 미생성)
pytest --swag-no-output

# dry-run — 문서를 stdout에 출력
pytest --swag --swag-dry-run
```

### 생성 규칙

- **`--swag` 플래그 필수**: 플래그 없이 실행하면 swag fixture는 동작하고 스키마 검증도 수행되지만, 파일 출력은 하지 않음. 즉 `swag`를 사용하는 테스트는 `--swag` 없이도 정상 실행되며, 문서 생성만 건너뛴다
- **충돌 처리**: 같은 엔드포인트에 대해 서로 다른 스키마가 정의되면 경고 출력 후 마지막 정의를 사용
- **실패한 테스트는 문서에서 제외**: 검증을 통과한 테스트의 스펙만 문서에 포함

## Security 스킴 및 인증

### Security 스킴 정의

```python
# conftest.py
@pytest.fixture(scope="session")
def swag_security_schemes():
    return {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Api-Key",
        },
    }
```

### 테스트에서 적용

```python
def test_create_blog(swag):
    swag.path("/blogs").post("Creates a blog")
    swag.security("BearerAuth")
    swag.response(201, schema={...})
    swag.response(401, description="Unauthorized")

    response = client.post("/blogs", json={...}, headers={"Authorization": "Bearer token"})
    swag.validate(response.status_code, response.json())
```

### 글로벌 security

```python
@pytest.fixture(scope="session")
def swag_config():
    return {
        "openapi": "3.1.0",
        "info": {"title": "Blog API", "version": "1.0.0"},
        "security": [{"BearerAuth": []}],  # 전체 API에 기본 적용
        "output_path": "docs/openapi.json",
    }
```

글로벌로 설정하면 개별 테스트에서 `swag.security()` 생략 가능. 특정 엔드포인트를 공개로 만들려면 `swag.security(None)`으로 오버라이드.

## 의존성

| 패키지 | 용도 | 필수 여부 |
|--------|------|-----------|
| `pytest` (>=7.0) | 플러그인 호스트 | 필수 |
| `jsonschema` | 응답 스키마 검증 | 필수 |
| `pyyaml` | YAML 출력 | 선택 (`[yaml]` extra) |

- `pip install pytest-swag` — JSON 출력만
- `pip install pytest-swag[yaml]` — YAML 출력 포함

## 테스트 전략

```
tests/
├── unit/
│   ├── test_builder.py       # DSL 빌더 메서드 단위 테스트
│   ├── test_validator.py     # 스키마 검증 로직 테스트
│   ├── test_collector.py     # 스펙 데이터 수집/병합 테스트
│   └── test_generator.py     # OpenAPI 문서 구조 생성 테스트
├── integration/
│   ├── test_plugin.py        # pytest 플러그인 통합 (pytester fixture 사용)
│   └── test_full_flow.py     # 테스트 실행 → 문서 생성 E2E
└── fixtures/
    └── expected_outputs/     # 기대하는 OpenAPI 출력 스냅샷
```

- **pytester**: pytest의 공식 플러그인 테스트 도구. 실제 pytest 세션을 실행하고 결과를 검증
- **스냅샷 테스트**: 생성된 OpenAPI 문서를 기대 출력과 비교

## 배포

- PyPI에 공개 배포 (오픈소스)
- MIT 라이센스
- OpenAPI 3.0 및 3.1 둘 다 지원
- 출력 포맷: JSON 및 YAML 둘 다 지원
