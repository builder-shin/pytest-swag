# pytest-swag

pytest 테스트에서 OpenAPI 문서를 자동 생성합니다.

pytest-swag는 pytest 테스트 코드에서 OpenAPI 문서를 자동 생성하는 **프레임워크 비의존** pytest 플러그인입니다. 빌더 DSL로 API 스펙을 정의하고, jsonschema로 응답을 검증한 뒤, 테스트 세션 종료 시 완전한 OpenAPI 문서를 출력합니다.

---

**[English](README.md) | 한국어**

---

### 설치

```bash
pip install pytest-swag
```

선택적 추가 패키지:

```bash
pip install pytest-swag[yaml]       # YAML 출력 지원
pip install pytest-swag[requests]   # requests 라이브러리 어댑터
pip install pytest-swag[dev]        # 개발 의존성
```

### 빠른 시작

```python
def test_get_blog(swag):
    swag.path("/blogs/{id}").get("블로그 조회")
    swag.parameter("id", in_="path", schema={"type": "string"})
    swag.response(200, schema={
        "type": "object",
        "properties": {"id": {"type": "integer"}, "title": {"type": "string"}},
    })

    response = client.get("/blogs/1")
    swag.validate(response.status_code, response.json())
```

`--swag` 플래그와 함께 테스트를 실행하세요:

```bash
pytest --swag
```

전체 API 스펙이 담긴 `openapi.json` 파일이 생성됩니다.

### 동작 원리

1. `swag` fixture의 빌더 DSL로 API 스펙을 **정의**
2. 각 응답을 선언된 스키마에 대해 jsonschema로 **검증**
3. 테스트 스위트 전체에서 검증된 operation을 **수집**
4. 세션 종료 시 완전한 OpenAPI 문서를 **생성**

검증에 통과한 테스트만 출력에 포함됩니다. 실패한 테스트는 자동으로 제외되어 문서의 정확성을 보장합니다.

### 설정

#### `pyproject.toml`로 설정

```toml
[tool.pytest-swag]
openapi = "3.1.0"
output_path = "docs/openapi.json"
output_format = "json"   # "json", "yaml", 또는 "both"

[tool.pytest-swag.info]
title = "My API"
version = "1.0.0"
```

#### `conftest.py` fixture로 설정

```python
import pytest

@pytest.fixture(scope="session")
def swag_config():
    return {
        "openapi": "3.1.0",
        "info": {"title": "My API", "version": "1.0.0"},
        "output_path": "docs/openapi.json",
        "output_format": "json",
        "servers": [{"url": "https://api.example.com/v1"}],
        "security": [{"BearerAuth": []}],
    }
```

### 빌더 DSL 레퍼런스

#### 경로 및 HTTP 메서드

```python
swag.path("/users").get("사용자 목록")
swag.path("/users").post("사용자 생성")
swag.path("/users/{id}").put("사용자 수정")
swag.path("/users/{id}").patch("사용자 부분 수정")
swag.path("/users/{id}").delete("사용자 삭제")
```

#### 파라미터

```python
# 경로 파라미터 (항상 필수)
swag.parameter("id", in_="path", schema={"type": "integer"})

# 쿼리 파라미터 (기본: 선택)
swag.parameter("page", in_="query", schema={"type": "integer"})

# 필수 헤더
swag.parameter("X-Api-Key", in_="header", schema={"type": "string"}, required=True)
```

#### 요청 본문

```python
swag.request_body(
    content_type="application/json",
    schema={
        "type": "object",
        "required": ["title"],
        "properties": {
            "title": {"type": "string"},
            "content": {"type": "string"},
        },
    },
)
```

#### 응답

```python
# 스키마 포함
swag.response(200, description="OK", schema={
    "type": "object",
    "properties": {"id": {"type": "integer"}},
})

# 스키마 없음 (예: 204 No Content)
swag.response(204, description="삭제됨")

# $ref 참조 (swag_schemas fixture 필요)
swag.response(200, schema={"$ref": "#/components/schemas/User"})
```

#### 태그 및 보안

```python
swag.tag("Users")
swag.security("BearerAuth")
```

#### 검증

```python
# 수동 검증
swag.validate(response.status_code, response.json())

# 다음을 검증합니다:
# 1. 상태 코드가 문서화되어 있는지
# 2. 응답 본문이 선언된 스키마와 일치하는지 (jsonschema)
```

### 컴포넌트 스키마 (`$ref` 지원)

`swag_schemas` fixture로 재사용 가능한 스키마를 정의합니다:

```python
@pytest.fixture(scope="session")
def swag_schemas():
    return {
        "User": {
            "type": "object",
            "required": ["id", "name"],
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
            },
        },
        "Error": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
            },
        },
    }
```

테스트에서 참조:

```python
def test_get_user(swag):
    swag.path("/users/{id}").get("사용자 조회")
    swag.parameter("id", in_="path", schema={"type": "integer"})
    swag.response(200, schema={"$ref": "#/components/schemas/User"})
    swag.response(404, schema={"$ref": "#/components/schemas/Error"})

    response = client.get("/users/1")
    swag.validate(response.status_code, response.json())
```

`$ref` 참조는 검증 시 재귀적으로 resolve되며, 생성된 OpenAPI 문서에는 원본 그대로 보존됩니다.

### 보안 스킴

```python
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
            "name": "X-API-Key",
        },
    }
```

### Requests 어댑터

`requests` 라이브러리를 사용하는 프로젝트에서는 `swag_requests` fixture로 응답을 자동 추출할 수 있습니다:

```python
def test_list_users(swag_requests):
    swag_requests.path("/users").get("사용자 목록")
    swag_requests.response(200, schema={
        "type": "array",
        "items": {"$ref": "#/components/schemas/User"},
    })

    response = requests.get("http://localhost:8000/users")
    swag_requests.validate_response(response)
    # response 객체에서 status_code와 JSON 본문을 자동으로 추출합니다
```

### 멀티 문서 출력

`swag.doc()`을 사용하여 하나의 테스트 스위트에서 여러 OpenAPI 문서를 생성할 수 있습니다:

```python
@pytest.fixture(scope="session")
def swag_config():
    return [
        {"info": {"title": "Public API", "version": "1.0.0"}, "output_path": "docs/public.json"},
        {"info": {"title": "Admin API", "version": "1.0.0"}, "output_path": "docs/admin.json"},
    ]

def test_public_endpoint(swag):
    swag.doc("Public API")
    swag.path("/posts").get("게시물 목록")
    swag.response(200, schema={"type": "array"})
    swag.validate(200, [])

def test_admin_endpoint(swag):
    swag.doc("Admin API")
    swag.path("/admin/users").get("전체 사용자 목록")
    swag.response(200, schema={"type": "array"})
    swag.validate(200, [])
```

### CLI 옵션

| 옵션 | 설명 |
|------|------|
| `--swag` | OpenAPI 문서 생성 활성화 |
| `--swag-output PATH` | 출력 파일 경로 덮어쓰기 |
| `--swag-dry-run` | 파일 대신 stdout으로 OpenAPI 문서 출력 |
| `--swag-no-output` | 검증만 수행, 파일 생성 건너뛰기 |
| `--swag-strict` | `swag` fixture를 사용하지만 `validate()`를 호출하지 않은 테스트에 대해 경고 |

### 전체 예제

```python
# conftest.py
import pytest

@pytest.fixture(scope="session")
def swag_config():
    return {
        "openapi": "3.1.0",
        "info": {"title": "Blog API", "version": "1.0.0"},
        "servers": [{"url": "https://api.example.com/v1"}],
        "security": [{"BearerAuth": []}],
        "output_path": "docs/openapi.json",
        "output_format": "both",
    }

@pytest.fixture(scope="session")
def swag_schemas():
    return {
        "Blog": {
            "type": "object",
            "required": ["id", "title"],
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string"},
                "content": {"type": "string"},
            },
        },
    }

@pytest.fixture(scope="session")
def swag_security_schemes():
    return {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
    }
```

```python
# test_blogs.py
def test_list_blogs(swag):
    swag.path("/blogs").get("블로그 목록")
    swag.tag("Blogs")
    swag.parameter("page", in_="query", schema={"type": "integer"})
    swag.response(200, schema={
        "type": "array",
        "items": {"$ref": "#/components/schemas/Blog"},
    })

    response = client.get("/blogs")
    swag.validate(response.status_code, response.json())

def test_create_blog(swag):
    swag.path("/blogs").post("블로그 생성")
    swag.tag("Blogs")
    swag.security("BearerAuth")
    swag.request_body(schema={
        "type": "object",
        "required": ["title"],
        "properties": {"title": {"type": "string"}, "content": {"type": "string"}},
    })
    swag.response(201, schema={"$ref": "#/components/schemas/Blog"})

    response = client.post("/blogs", json={"title": "Hello", "content": "World"})
    swag.validate(response.status_code, response.json())

def test_delete_blog(swag):
    swag.path("/blogs/{id}").delete("블로그 삭제")
    swag.tag("Blogs")
    swag.parameter("id", in_="path", schema={"type": "integer"})
    swag.response(204, description="삭제됨")

    response = client.delete("/blogs/1")
    swag.validate(response.status_code, None)
```

```bash
pytest --swag
# docs/openapi.json과 docs/openapi.yaml이 생성됩니다
```

### 요구 사항

- Python >= 3.10
- pytest >= 7.0
- jsonschema >= 4.0
- PyYAML >= 6.0 (선택, YAML 출력용)

### 감사의 말

pytest-swag는 Ruby/RSpec 기반의 Swagger/OpenAPI 문서 자동 생성 라이브러리인 [rswag](https://github.com/rswag/rswag)에서 영감을 받았습니다. 테스트와 API 문서 사이의 간극을 잇는 "테스트 주도 문서화(test-driven documentation)" 접근법을 개척한 rswag 팀에 깊은 감사를 드립니다. pytest-swag는 이 철학을 Python/pytest 생태계로 가져옵니다.

### 라이선스

MIT
