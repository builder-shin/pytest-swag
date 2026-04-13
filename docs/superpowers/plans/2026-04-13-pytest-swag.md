# pytest-swag Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** pytest 테스트 코드에서 OpenAPI 문서를 자동 생성하는 프레임워크 비의존 pytest 플러그인을 만든다.

**Architecture:** pytest fixture 기반 빌더 패턴으로 API 스펙을 정의하고, jsonschema로 응답을 검증한 뒤, pytest session 종료 시 OpenAPI 3.0/3.1 문서를 JSON/YAML로 출력한다. 코어는 config → builder → validator → collector → generator 파이프라인으로 구성된다.

**Tech Stack:** Python 3.10+, pytest >=7.0, jsonschema, PyYAML (optional)

---

## File Structure

```
pytest-swag/
├── src/
│   └── pytest_swag/
│       ├── __init__.py          # 공개 API: SwagBuilder, SwagValidationError export
│       ├── plugin.py            # pytest 플러그인: fixture 등록, CLI 옵션, session hooks
│       ├── builder.py           # SwagBuilder: DSL 메서드 (path, parameter, response 등)
│       ├── collector.py         # SwagCollector: 테스트별 스펙 데이터 수집/병합
│       ├── generator.py         # SwagGenerator: 수집 데이터 → OpenAPI dict → 파일 출력
│       ├── validator.py         # SwagValidator: jsonschema 기반 응답 검증
│       ├── schema.py            # OpenAPI 스키마 상수/유틸 (버전별 기본 구조)
│       ├── config.py            # SwagConfig: pyproject.toml + fixture 설정 병합
│       └── adapters/
│           ├── __init__.py      # 어댑터 공통 인터페이스
│           └── requests.py      # requests 라이브러리 자동 연동 어댑터
├── tests/
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_builder.py
│   │   ├── test_validator.py
│   │   ├── test_collector.py
│   │   ├── test_generator.py
│   │   └── test_adapter_requests.py
│   ├── integration/
│   │   ├── test_plugin.py
│   │   └── test_full_flow.py
│   └── conftest.py
├── pyproject.toml
├── LICENSE
└── README.md
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/pytest_swag/__init__.py`
- Create: `LICENSE`
- Create: `README.md`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "pytest-swag"
version = "0.1.0"
description = "Generate OpenAPI documentation from pytest tests"
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
authors = [
    { name = "jwshin" },
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Framework :: Pytest",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Testing",
]
dependencies = [
    "pytest>=7.0",
    "jsonschema>=4.0",
]

[project.optional-dependencies]
yaml = ["pyyaml>=6.0"]
requests = ["requests>=2.20"]
dev = [
    "pyyaml>=6.0",
    "requests>=2.20",
    "ruff>=0.4",
]

[project.entry-points.pytest11]
swag = "pytest_swag.plugin"

[project.urls]
Homepage = "https://github.com/jwshin/pytest-swag"
Repository = "https://github.com/jwshin/pytest-swag"

[tool.hatch.build.targets.wheel]
packages = ["src/pytest_swag"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
target-version = "py310"
line-length = 100
```

- [ ] **Step 2: Create LICENSE (MIT)**

```
MIT License

Copyright (c) 2026 jwshin

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: Create minimal README.md**

```markdown
# pytest-swag

Generate OpenAPI documentation from pytest tests.

## Installation

```bash
pip install pytest-swag
```

## Quick Start

```python
def test_get_blog(swag):
    swag.path("/blogs/{id}").get("Retrieves a blog")
    swag.parameter("id", in_="path", schema={"type": "string"})
    swag.response(200, schema={"type": "object", "properties": {"id": {"type": "integer"}}})

    response = client.get("/blogs/1")
    swag.validate(response.status_code, response.json())
```

Run with `pytest --swag` to generate OpenAPI documentation.
```

- [ ] **Step 4: Create src/pytest_swag/__init__.py**

```python
"""pytest-swag: Generate OpenAPI documentation from pytest tests."""

__version__ = "0.1.0"
```

- [ ] **Step 5: Create tests/conftest.py**

```python
pytest_plugins = ["pytester"]
```

- [ ] **Step 6: Install project in dev mode and verify**

Run: `cd /Users/jwshin/Desktop/develop/workspace/builder-shin/library/python/pytest-swag && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
Expected: Install succeeds, `pytest --co` runs without error

- [ ] **Step 7: Initialize git and commit**

```bash
git init
echo -e ".venv/\n__pycache__/\n*.egg-info/\ndist/\nbuild/\n.pytest_cache/\n*.pyc" > .gitignore
git add .gitignore pyproject.toml LICENSE README.md src/pytest_swag/__init__.py tests/conftest.py
git commit -m "feat: project scaffolding with pyproject.toml and src layout"
```

---

### Task 2: Config Module

**Files:**
- Create: `src/pytest_swag/config.py`
- Create: `tests/unit/test_config.py`

- [ ] **Step 1: Write failing tests for SwagConfig**

`tests/unit/test_config.py`:

```python
import pytest
from pytest_swag.config import SwagConfig


class TestSwagConfigDefaults:
    def test_default_openapi_version(self):
        config = SwagConfig()
        assert config.openapi == "3.1.0"

    def test_default_info(self):
        config = SwagConfig()
        assert config.info == {"title": "API", "version": "0.1.0"}

    def test_default_output_path(self):
        config = SwagConfig()
        assert config.output_path == "openapi.json"

    def test_default_output_format(self):
        config = SwagConfig()
        assert config.output_format == "json"


class TestSwagConfigFromDict:
    def test_from_dict_overrides_defaults(self):
        config = SwagConfig.from_dict({
            "openapi": "3.0.3",
            "info": {"title": "Blog API", "version": "1.0.0"},
            "output_path": "docs/api.json",
            "output_format": "both",
        })
        assert config.openapi == "3.0.3"
        assert config.info == {"title": "Blog API", "version": "1.0.0"}
        assert config.output_path == "docs/api.json"
        assert config.output_format == "both"

    def test_from_dict_partial_override(self):
        config = SwagConfig.from_dict({"openapi": "3.0.3"})
        assert config.openapi == "3.0.3"
        assert config.info == {"title": "API", "version": "0.1.0"}

    def test_from_dict_with_servers(self):
        config = SwagConfig.from_dict({
            "servers": [{"url": "https://api.example.com"}],
        })
        assert config.servers == [{"url": "https://api.example.com"}]

    def test_from_dict_with_security(self):
        config = SwagConfig.from_dict({
            "security": [{"BearerAuth": []}],
        })
        assert config.security == [{"BearerAuth": []}]


class TestSwagConfigFromPyproject:
    def test_reads_tool_pytest_swag_section(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.pytest-swag]\n'
            'openapi = "3.0.3"\n'
            'output_path = "docs/api.yaml"\n'
            'output_format = "yaml"\n'
            '\n'
            '[tool.pytest-swag.info]\n'
            'title = "My API"\n'
            'version = "2.0.0"\n'
        )
        config = SwagConfig.from_pyproject(tmp_path)
        assert config.openapi == "3.0.3"
        assert config.info == {"title": "My API", "version": "2.0.0"}
        assert config.output_path == "docs/api.yaml"
        assert config.output_format == "yaml"

    def test_returns_defaults_when_no_pyproject(self, tmp_path):
        config = SwagConfig.from_pyproject(tmp_path)
        assert config.openapi == "3.1.0"

    def test_returns_defaults_when_no_section(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.ruff]\nline-length = 100\n')
        config = SwagConfig.from_pyproject(tmp_path)
        assert config.openapi == "3.1.0"


class TestSwagConfigMultiDoc:
    def test_from_list_creates_multiple_configs(self):
        configs = SwagConfig.from_list([
            {"info": {"title": "API v1", "version": "1.0.0"}, "output_path": "v1.json"},
            {"info": {"title": "API v2", "version": "2.0.0"}, "output_path": "v2.json"},
        ])
        assert len(configs) == 2
        assert configs[0].info["title"] == "API v1"
        assert configs[1].info["title"] == "API v2"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pytest_swag.config'`

- [ ] **Step 3: Implement SwagConfig**

`src/pytest_swag/config.py`:

```python
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


_DEFAULTS = {
    "openapi": "3.1.0",
    "info": {"title": "API", "version": "0.1.0"},
    "output_path": "openapi.json",
    "output_format": "json",
    "servers": [],
    "security": [],
}


@dataclass
class SwagConfig:
    openapi: str = _DEFAULTS["openapi"]
    info: dict = field(default_factory=lambda: dict(_DEFAULTS["info"]))
    output_path: str = _DEFAULTS["output_path"]
    output_format: str = _DEFAULTS["output_format"]
    servers: list[dict] = field(default_factory=list)
    security: list[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> SwagConfig:
        return cls(
            openapi=data.get("openapi", _DEFAULTS["openapi"]),
            info=data.get("info", dict(_DEFAULTS["info"])),
            output_path=data.get("output_path", _DEFAULTS["output_path"]),
            output_format=data.get("output_format", _DEFAULTS["output_format"]),
            servers=data.get("servers", []),
            security=data.get("security", []),
        )

    @classmethod
    def from_pyproject(cls, root: Path) -> SwagConfig:
        pyproject_path = root / "pyproject.toml"
        if not pyproject_path.exists():
            return cls()
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        section = data.get("tool", {}).get("pytest-swag", {})
        if not section:
            return cls()
        info = section.pop("info", None)
        result = dict(section)
        if info:
            result["info"] = info
        return cls.from_dict(result)

    @classmethod
    def from_list(cls, items: list[dict]) -> list[SwagConfig]:
        return [cls.from_dict(item) for item in items]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_config.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/pytest_swag/config.py tests/unit/test_config.py
git commit -m "feat: add SwagConfig with pyproject.toml and fixture support"
```

---

### Task 3: Schema Utilities

**Files:**
- Create: `src/pytest_swag/schema.py`
- Create: `tests/unit/test_schema.py`

- [ ] **Step 1: Write failing tests for schema utilities**

`tests/unit/test_schema.py`:

```python
from pytest_swag.schema import make_openapi_skeleton


class TestMakeOpenAPISkeleton:
    def test_skeleton_30(self):
        result = make_openapi_skeleton(
            openapi="3.0.3",
            info={"title": "Test", "version": "1.0.0"},
        )
        assert result["openapi"] == "3.0.3"
        assert result["info"] == {"title": "Test", "version": "1.0.0"}
        assert result["paths"] == {}
        assert "components" not in result

    def test_skeleton_31(self):
        result = make_openapi_skeleton(
            openapi="3.1.0",
            info={"title": "Test", "version": "1.0.0"},
        )
        assert result["openapi"] == "3.1.0"

    def test_skeleton_with_servers(self):
        result = make_openapi_skeleton(
            openapi="3.1.0",
            info={"title": "Test", "version": "1.0.0"},
            servers=[{"url": "https://api.example.com"}],
        )
        assert result["servers"] == [{"url": "https://api.example.com"}]

    def test_skeleton_with_security(self):
        result = make_openapi_skeleton(
            openapi="3.1.0",
            info={"title": "Test", "version": "1.0.0"},
            security=[{"BearerAuth": []}],
        )
        assert result["security"] == [{"BearerAuth": []}]

    def test_skeleton_without_optional_fields(self):
        result = make_openapi_skeleton(
            openapi="3.1.0",
            info={"title": "Test", "version": "1.0.0"},
        )
        assert "servers" not in result
        assert "security" not in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_schema.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement schema utilities**

`src/pytest_swag/schema.py`:

```python
from __future__ import annotations


def make_openapi_skeleton(
    *,
    openapi: str,
    info: dict,
    servers: list[dict] | None = None,
    security: list[dict] | None = None,
) -> dict:
    doc: dict = {
        "openapi": openapi,
        "info": info,
        "paths": {},
    }
    if servers:
        doc["servers"] = servers
    if security:
        doc["security"] = security
    return doc
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_schema.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/pytest_swag/schema.py tests/unit/test_schema.py
git commit -m "feat: add OpenAPI skeleton builder utility"
```

---

### Task 4: SwagBuilder DSL

**Files:**
- Create: `src/pytest_swag/builder.py`
- Create: `tests/unit/test_builder.py`

- [ ] **Step 1: Write failing tests for SwagBuilder**

`tests/unit/test_builder.py`:

```python
import pytest
from pytest_swag.builder import SwagBuilder


class TestPath:
    def test_path_get(self):
        b = SwagBuilder()
        b.path("/blogs").get("List blogs")
        assert b._path == "/blogs"
        assert b._method == "get"
        assert b._summary == "List blogs"

    def test_path_post(self):
        b = SwagBuilder()
        b.path("/blogs").post("Create blog")
        assert b._method == "post"

    def test_path_put(self):
        b = SwagBuilder()
        b.path("/blogs/{id}").put("Update blog")
        assert b._method == "put"

    def test_path_patch(self):
        b = SwagBuilder()
        b.path("/blogs/{id}").patch("Patch blog")
        assert b._method == "patch"

    def test_path_delete(self):
        b = SwagBuilder()
        b.path("/blogs/{id}").delete("Delete blog")
        assert b._method == "delete"


class TestTag:
    def test_single_tag(self):
        b = SwagBuilder()
        b.tag("Blogs")
        assert b._tags == ["Blogs"]

    def test_multiple_tags(self):
        b = SwagBuilder()
        b.tag("Blogs")
        b.tag("Admin")
        assert b._tags == ["Blogs", "Admin"]


class TestParameter:
    def test_path_parameter(self):
        b = SwagBuilder()
        b.parameter("id", in_="path", schema={"type": "string"})
        assert len(b._parameters) == 1
        assert b._parameters[0] == {
            "name": "id",
            "in": "path",
            "required": True,
            "schema": {"type": "string"},
        }

    def test_path_parameter_always_required(self):
        b = SwagBuilder()
        b.parameter("id", in_="path", schema={"type": "string"}, required=False)
        assert b._parameters[0]["required"] is True

    def test_header_parameter(self):
        b = SwagBuilder()
        b.parameter("X-Api-Key", in_="header", schema={"type": "string"}, required=True)
        assert b._parameters[0]["required"] is True
        assert b._parameters[0]["in"] == "header"

    def test_query_parameter_optional_by_default(self):
        b = SwagBuilder()
        b.parameter("page", in_="query", schema={"type": "integer"})
        assert b._parameters[0]["required"] is False


class TestRequestBody:
    def test_request_body(self):
        b = SwagBuilder()
        schema = {"type": "object", "properties": {"title": {"type": "string"}}}
        b.request_body(content_type="application/json", schema=schema)
        assert b._request_body == {
            "content": {
                "application/json": {"schema": schema},
            },
        }


class TestResponse:
    def test_response_with_schema(self):
        b = SwagBuilder()
        schema = {"type": "object", "properties": {"id": {"type": "integer"}}}
        b.response(200, description="OK", schema=schema)
        assert 200 in b._responses
        assert b._responses[200]["description"] == "OK"
        assert b._responses[200]["schema"] == schema

    def test_response_without_schema(self):
        b = SwagBuilder()
        b.response(204, description="No content")
        assert b._responses[204] == {"description": "No content", "schema": None}

    def test_default_description(self):
        b = SwagBuilder()
        b.response(200, schema={"type": "object"})
        assert b._responses[200]["description"] == "OK"


class TestSecurity:
    def test_security(self):
        b = SwagBuilder()
        b.security("BearerAuth")
        assert b._security == [{"BearerAuth": []}]

    def test_security_none_override(self):
        b = SwagBuilder()
        b.security(None)
        assert b._security == []

    def test_multiple_security(self):
        b = SwagBuilder()
        b.security("BearerAuth")
        b.security("ApiKeyAuth")
        assert b._security == [{"BearerAuth": []}, {"ApiKeyAuth": []}]


class TestDoc:
    def test_doc_target(self):
        b = SwagBuilder()
        b.doc("Blog API v2")
        assert b._doc_target == "Blog API v2"

    def test_doc_target_default_none(self):
        b = SwagBuilder()
        assert b._doc_target is None


class TestToOperationDict:
    def test_full_operation(self):
        b = SwagBuilder()
        b.path("/blogs").post("Create blog")
        b.tag("Blogs")
        b.parameter("X-Api-Key", in_="header", schema={"type": "string"}, required=True)
        b.request_body(
            content_type="application/json",
            schema={"type": "object", "properties": {"title": {"type": "string"}}},
        )
        b.response(201, description="Created", schema={"type": "object"})
        b.security("BearerAuth")

        op = b.to_operation_dict()
        assert op["path"] == "/blogs"
        assert op["method"] == "post"
        assert op["summary"] == "Create blog"
        assert op["tags"] == ["Blogs"]
        assert len(op["parameters"]) == 1
        assert "requestBody" in op
        assert 201 in op["responses"]
        assert op["security"] == [{"BearerAuth": []}]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_builder.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement SwagBuilder**

`src/pytest_swag/builder.py`:

```python
from __future__ import annotations

from http import HTTPStatus


class _PathProxy:
    def __init__(self, builder: SwagBuilder, path: str) -> None:
        self._builder = builder
        self._builder._path = path

    def _set_method(self, method: str, summary: str) -> SwagBuilder:
        self._builder._method = method
        self._builder._summary = summary
        return self._builder

    def get(self, summary: str = "") -> SwagBuilder:
        return self._set_method("get", summary)

    def post(self, summary: str = "") -> SwagBuilder:
        return self._set_method("post", summary)

    def put(self, summary: str = "") -> SwagBuilder:
        return self._set_method("put", summary)

    def patch(self, summary: str = "") -> SwagBuilder:
        return self._set_method("patch", summary)

    def delete(self, summary: str = "") -> SwagBuilder:
        return self._set_method("delete", summary)


class SwagBuilder:
    def __init__(self) -> None:
        self._path: str | None = None
        self._method: str | None = None
        self._summary: str = ""
        self._tags: list[str] = []
        self._parameters: list[dict] = []
        self._request_body: dict | None = None
        self._responses: dict[int, dict] = {}
        self._security: list[dict] | None = None
        self._doc_target: str | None = None
        self._validated: bool = False

    def path(self, path: str) -> _PathProxy:
        return _PathProxy(self, path)

    def tag(self, name: str) -> SwagBuilder:
        self._tags.append(name)
        return self

    def parameter(
        self,
        name: str,
        *,
        in_: str,
        schema: dict,
        required: bool | None = None,
    ) -> SwagBuilder:
        if in_ == "path":
            required = True
        elif required is None:
            required = False
        self._parameters.append({
            "name": name,
            "in": in_,
            "required": required,
            "schema": schema,
        })
        return self

    def request_body(
        self,
        *,
        content_type: str = "application/json",
        schema: dict,
    ) -> SwagBuilder:
        self._request_body = {
            "content": {
                content_type: {"schema": schema},
            },
        }
        return self

    def response(
        self,
        status_code: int,
        *,
        description: str | None = None,
        schema: dict | None = None,
    ) -> SwagBuilder:
        if description is None:
            try:
                description = HTTPStatus(status_code).phrase
            except ValueError:
                description = ""
        self._responses[status_code] = {
            "description": description,
            "schema": schema,
        }
        return self

    def security(self, scheme: str | None) -> SwagBuilder:
        if self._security is None:
            self._security = []
        if scheme is None:
            self._security = []
        else:
            self._security.append({scheme: []})
        return self

    def doc(self, target: str) -> SwagBuilder:
        self._doc_target = target
        return self

    def to_operation_dict(self) -> dict:
        op: dict = {
            "path": self._path,
            "method": self._method,
            "summary": self._summary,
        }
        if self._tags:
            op["tags"] = self._tags
        if self._parameters:
            op["parameters"] = self._parameters
        if self._request_body:
            op["requestBody"] = self._request_body
        responses: dict[int, dict] = {}
        for code, resp in self._responses.items():
            entry: dict = {"description": resp["description"]}
            if resp["schema"] is not None:
                entry["content"] = {
                    "application/json": {"schema": resp["schema"]},
                }
            responses[code] = entry
        op["responses"] = responses
        if self._security is not None:
            op["security"] = self._security
        return op
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_builder.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/pytest_swag/builder.py tests/unit/test_builder.py
git commit -m "feat: add SwagBuilder DSL with path chaining and operation builder"
```

---

### Task 5: Validator

**Files:**
- Create: `src/pytest_swag/validator.py`
- Create: `tests/unit/test_validator.py`

- [ ] **Step 1: Write failing tests for SwagValidator**

`tests/unit/test_validator.py`:

```python
import pytest
from pytest_swag.validator import SwagValidator, SwagValidationError


class TestValidateStatusCode:
    def test_valid_status_code(self):
        v = SwagValidator(
            responses={200: {"description": "OK", "schema": None}},
            path="/blogs",
            method="get",
        )
        v.validate(200, {})  # should not raise

    def test_undocumented_status_code(self):
        v = SwagValidator(
            responses={200: {"description": "OK", "schema": None}},
            path="/blogs",
            method="get",
        )
        with pytest.raises(SwagValidationError, match="Undocumented status code: 404"):
            v.validate(404, {})


class TestValidateSchema:
    def test_valid_body(self):
        schema = {
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "integer"}},
        }
        v = SwagValidator(
            responses={200: {"description": "OK", "schema": schema}},
            path="/blogs",
            method="get",
        )
        v.validate(200, {"id": 1})  # should not raise

    def test_invalid_body_wrong_type(self):
        schema = {
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "integer"}},
        }
        v = SwagValidator(
            responses={200: {"description": "OK", "schema": schema}},
            path="/blogs",
            method="get",
        )
        with pytest.raises(SwagValidationError, match="Schema validation failed"):
            v.validate(200, {"id": "not_an_int"})

    def test_missing_required_field(self):
        schema = {
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "integer"}},
        }
        v = SwagValidator(
            responses={200: {"description": "OK", "schema": schema}},
            path="/blogs",
            method="get",
        )
        with pytest.raises(SwagValidationError, match="Schema validation failed"):
            v.validate(200, {})

    def test_no_schema_skips_validation(self):
        v = SwagValidator(
            responses={204: {"description": "No content", "schema": None}},
            path="/blogs/{id}",
            method="delete",
        )
        v.validate(204, None)  # should not raise


class TestValidateWithRef:
    def test_ref_resolved_against_component_schemas(self):
        schema = {"$ref": "#/components/schemas/Blog"}
        component_schemas = {
            "Blog": {
                "type": "object",
                "required": ["id"],
                "properties": {"id": {"type": "integer"}},
            }
        }
        v = SwagValidator(
            responses={200: {"description": "OK", "schema": schema}},
            path="/blogs/{id}",
            method="get",
            component_schemas=component_schemas,
        )
        v.validate(200, {"id": 1})  # should not raise

    def test_ref_validation_failure(self):
        schema = {"$ref": "#/components/schemas/Blog"}
        component_schemas = {
            "Blog": {
                "type": "object",
                "required": ["id"],
                "properties": {"id": {"type": "integer"}},
            }
        }
        v = SwagValidator(
            responses={200: {"description": "OK", "schema": schema}},
            path="/blogs/{id}",
            method="get",
            component_schemas=component_schemas,
        )
        with pytest.raises(SwagValidationError, match="Schema validation failed"):
            v.validate(200, {"id": "not_int"})


class TestErrorMessage:
    def test_error_includes_path_and_method(self):
        schema = {"type": "object", "properties": {"id": {"type": "integer"}}}
        v = SwagValidator(
            responses={200: {"description": "OK", "schema": schema}},
            path="/blogs",
            method="post",
        )
        with pytest.raises(SwagValidationError, match="POST /blogs"):
            v.validate(200, {"id": "wrong"})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_validator.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement SwagValidator**

`src/pytest_swag/validator.py`:

```python
from __future__ import annotations

import jsonschema


class SwagValidationError(AssertionError):
    pass


class SwagValidator:
    def __init__(
        self,
        *,
        responses: dict[int, dict],
        path: str,
        method: str,
        component_schemas: dict | None = None,
    ) -> None:
        self._responses = responses
        self._path = path
        self._method = method.upper()
        self._component_schemas = component_schemas or {}

    def validate(self, status_code: int, body: object) -> None:
        if status_code not in self._responses:
            raise SwagValidationError(
                f"Undocumented status code: {status_code} for {self._method} {self._path}"
            )
        schema = self._responses[status_code].get("schema")
        if schema is None or body is None:
            return
        resolved_schema = self._resolve_schema(schema)
        try:
            jsonschema.validate(instance=body, schema=resolved_schema)
        except jsonschema.ValidationError as e:
            raise SwagValidationError(
                f"Schema validation failed for {self._method} {self._path} → {status_code}\n\n"
                f"Path: $.{'.'.join(str(p) for p in e.absolute_path)}\n"
                f"Error: {e.message}"
            ) from None

    def _resolve_schema(self, schema: dict) -> dict:
        if "$ref" not in schema:
            return schema
        ref = schema["$ref"]
        prefix = "#/components/schemas/"
        if not ref.startswith(prefix):
            return schema
        name = ref[len(prefix):]
        resolved = self._component_schemas.get(name)
        if resolved is None:
            raise SwagValidationError(
                f"Unresolved $ref: {ref} — schema '{name}' not found in component_schemas"
            )
        return resolved
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_validator.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/pytest_swag/validator.py tests/unit/test_validator.py
git commit -m "feat: add SwagValidator with jsonschema validation and $ref support"
```

---

### Task 6: Collector

**Files:**
- Create: `src/pytest_swag/collector.py`
- Create: `tests/unit/test_collector.py`

- [ ] **Step 1: Write failing tests for SwagCollector**

`tests/unit/test_collector.py`:

```python
import pytest
from pytest_swag.collector import SwagCollector


class TestCollect:
    def test_collect_single_operation(self):
        c = SwagCollector()
        c.collect({
            "path": "/blogs",
            "method": "get",
            "summary": "List blogs",
            "responses": {200: {"description": "OK"}},
        })
        ops = c.get_operations()
        assert len(ops) == 1
        assert ops[0]["path"] == "/blogs"

    def test_collect_multiple_operations(self):
        c = SwagCollector()
        c.collect({
            "path": "/blogs",
            "method": "get",
            "summary": "List",
            "responses": {200: {"description": "OK"}},
        })
        c.collect({
            "path": "/blogs",
            "method": "post",
            "summary": "Create",
            "responses": {201: {"description": "Created"}},
        })
        ops = c.get_operations()
        assert len(ops) == 2


class TestMerge:
    def test_merge_same_path_different_methods(self):
        c = SwagCollector()
        c.collect({
            "path": "/blogs",
            "method": "get",
            "summary": "List",
            "responses": {200: {"description": "OK"}},
        })
        c.collect({
            "path": "/blogs",
            "method": "post",
            "summary": "Create",
            "responses": {201: {"description": "Created"}},
        })
        paths = c.merge_to_paths()
        assert "/blogs" in paths
        assert "get" in paths["/blogs"]
        assert "post" in paths["/blogs"]

    def test_merge_same_path_same_method_different_responses(self):
        c = SwagCollector()
        c.collect({
            "path": "/blogs",
            "method": "get",
            "summary": "List",
            "responses": {200: {"description": "OK", "content": {"application/json": {"schema": {"type": "array"}}}}},
        })
        c.collect({
            "path": "/blogs",
            "method": "get",
            "summary": "List",
            "responses": {404: {"description": "Not found"}},
        })
        paths = c.merge_to_paths()
        method_obj = paths["/blogs"]["get"]
        assert 200 in method_obj["responses"]
        assert 404 in method_obj["responses"]


class TestDocTarget:
    def test_collect_with_doc_target(self):
        c = SwagCollector()
        c.collect({
            "path": "/blogs",
            "method": "get",
            "summary": "List",
            "responses": {200: {"description": "OK"}},
            "doc_target": "API v2",
        })
        ops = c.get_operations(doc_target="API v2")
        assert len(ops) == 1

    def test_filter_by_doc_target(self):
        c = SwagCollector()
        c.collect({
            "path": "/v1/blogs",
            "method": "get",
            "summary": "List v1",
            "responses": {200: {"description": "OK"}},
            "doc_target": "API v1",
        })
        c.collect({
            "path": "/v2/blogs",
            "method": "get",
            "summary": "List v2",
            "responses": {200: {"description": "OK"}},
            "doc_target": "API v2",
        })
        assert len(c.get_operations(doc_target="API v1")) == 1
        assert len(c.get_operations(doc_target="API v2")) == 1

    def test_no_target_defaults_to_none(self):
        c = SwagCollector()
        c.collect({
            "path": "/blogs",
            "method": "get",
            "summary": "List",
            "responses": {200: {"description": "OK"}},
        })
        ops = c.get_operations(doc_target=None)
        assert len(ops) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_collector.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement SwagCollector**

`src/pytest_swag/collector.py`:

```python
from __future__ import annotations

import warnings


class SwagCollector:
    def __init__(self) -> None:
        self._operations: list[dict] = []

    def collect(self, operation: dict) -> None:
        self._operations.append(operation)

    def get_operations(self, *, doc_target: str | None = None) -> list[dict]:
        return [
            op for op in self._operations
            if op.get("doc_target") == doc_target
        ]

    def merge_to_paths(self, *, doc_target: str | None = None) -> dict:
        paths: dict = {}
        for op in self.get_operations(doc_target=doc_target):
            path = op["path"]
            method = op["method"]
            if path not in paths:
                paths[path] = {}
            if method in paths[path]:
                existing = paths[path][method]
                for code, resp in op["responses"].items():
                    if code in existing["responses"]:
                        warnings.warn(
                            f"Conflicting schema for {method.upper()} {path} → {code}. "
                            f"Using latest definition.",
                            stacklevel=2,
                        )
                    existing["responses"][code] = resp
            else:
                method_obj: dict = {"summary": op.get("summary", "")}
                if op.get("tags"):
                    method_obj["tags"] = op["tags"]
                if op.get("parameters"):
                    method_obj["parameters"] = op["parameters"]
                if op.get("requestBody"):
                    method_obj["requestBody"] = op["requestBody"]
                method_obj["responses"] = dict(op.get("responses", {}))
                if op.get("security") is not None:
                    method_obj["security"] = op["security"]
                paths[path][method] = method_obj
        return paths
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_collector.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/pytest_swag/collector.py tests/unit/test_collector.py
git commit -m "feat: add SwagCollector with operation merging and multi-doc support"
```

---

### Task 7: Generator

**Files:**
- Create: `src/pytest_swag/generator.py`
- Create: `tests/unit/test_generator.py`

- [ ] **Step 1: Write failing tests for SwagGenerator**

`tests/unit/test_generator.py`:

```python
import json
from pathlib import Path

import pytest
from pytest_swag.config import SwagConfig
from pytest_swag.generator import SwagGenerator


class TestGenerateDoc:
    def test_generates_valid_openapi_structure(self):
        config = SwagConfig.from_dict({
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
        })
        paths = {
            "/blogs": {
                "get": {
                    "summary": "List blogs",
                    "responses": {
                        200: {"description": "OK"},
                    },
                },
            },
        }
        gen = SwagGenerator(config=config, paths=paths)
        doc = gen.generate()
        assert doc["openapi"] == "3.1.0"
        assert doc["info"]["title"] == "Test API"
        assert "/blogs" in doc["paths"]

    def test_responses_keys_are_strings(self):
        config = SwagConfig()
        paths = {
            "/blogs": {
                "get": {
                    "summary": "List",
                    "responses": {200: {"description": "OK"}},
                },
            },
        }
        gen = SwagGenerator(config=config, paths=paths)
        doc = gen.generate()
        responses = doc["paths"]["/blogs"]["get"]["responses"]
        assert "200" in responses
        assert 200 not in responses


class TestComponentSchemas:
    def test_includes_component_schemas(self):
        config = SwagConfig()
        schemas = {
            "Blog": {
                "type": "object",
                "properties": {"id": {"type": "integer"}},
            }
        }
        gen = SwagGenerator(config=config, paths={}, component_schemas=schemas)
        doc = gen.generate()
        assert doc["components"]["schemas"]["Blog"]["type"] == "object"

    def test_no_components_when_empty(self):
        config = SwagConfig()
        gen = SwagGenerator(config=config, paths={})
        doc = gen.generate()
        assert "components" not in doc


class TestSecuritySchemes:
    def test_includes_security_schemes(self):
        config = SwagConfig()
        security_schemes = {
            "BearerAuth": {"type": "http", "scheme": "bearer"},
        }
        gen = SwagGenerator(config=config, paths={}, security_schemes=security_schemes)
        doc = gen.generate()
        assert doc["components"]["securitySchemes"]["BearerAuth"]["type"] == "http"


class TestWriteFile:
    def test_write_json(self, tmp_path):
        config = SwagConfig.from_dict({"output_path": str(tmp_path / "api.json"), "output_format": "json"})
        paths = {"/blogs": {"get": {"summary": "List", "responses": {200: {"description": "OK"}}}}}
        gen = SwagGenerator(config=config, paths=paths)
        gen.write()
        output = tmp_path / "api.json"
        assert output.exists()
        data = json.loads(output.read_text())
        assert data["paths"]["/blogs"]["get"]["summary"] == "List"

    def test_write_yaml(self, tmp_path):
        pytest.importorskip("yaml")
        import yaml

        config = SwagConfig.from_dict({"output_path": str(tmp_path / "api.yaml"), "output_format": "yaml"})
        paths = {"/blogs": {"get": {"summary": "List", "responses": {200: {"description": "OK"}}}}}
        gen = SwagGenerator(config=config, paths=paths)
        gen.write()
        output = tmp_path / "api.yaml"
        assert output.exists()
        data = yaml.safe_load(output.read_text())
        assert data["paths"]["/blogs"]["get"]["summary"] == "List"

    def test_write_both(self, tmp_path):
        pytest.importorskip("yaml")
        config = SwagConfig.from_dict({
            "output_path": str(tmp_path / "api.json"),
            "output_format": "both",
        })
        paths = {"/blogs": {"get": {"summary": "List", "responses": {200: {"description": "OK"}}}}}
        gen = SwagGenerator(config=config, paths=paths)
        gen.write()
        assert (tmp_path / "api.json").exists()
        assert (tmp_path / "api.yaml").exists()

    def test_creates_parent_directories(self, tmp_path):
        config = SwagConfig.from_dict({
            "output_path": str(tmp_path / "docs" / "nested" / "api.json"),
        })
        gen = SwagGenerator(config=config, paths={})
        gen.write()
        assert (tmp_path / "docs" / "nested" / "api.json").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_generator.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement SwagGenerator**

`src/pytest_swag/generator.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from pytest_swag.config import SwagConfig
from pytest_swag.schema import make_openapi_skeleton


class SwagGenerator:
    def __init__(
        self,
        *,
        config: SwagConfig,
        paths: dict,
        component_schemas: dict | None = None,
        security_schemes: dict | None = None,
    ) -> None:
        self._config = config
        self._paths = paths
        self._component_schemas = component_schemas or {}
        self._security_schemes = security_schemes or {}

    def generate(self) -> dict:
        doc = make_openapi_skeleton(
            openapi=self._config.openapi,
            info=self._config.info,
            servers=self._config.servers or None,
            security=self._config.security or None,
        )
        doc["paths"] = self._convert_paths(self._paths)
        components: dict = {}
        if self._component_schemas:
            components["schemas"] = self._component_schemas
        if self._security_schemes:
            components["securitySchemes"] = self._security_schemes
        if components:
            doc["components"] = components
        return doc

    def _convert_paths(self, paths: dict) -> dict:
        converted: dict = {}
        for path, methods in paths.items():
            converted[path] = {}
            for method, operation in methods.items():
                op = dict(operation)
                if "responses" in op:
                    op["responses"] = {
                        str(code): resp
                        for code, resp in op["responses"].items()
                    }
                converted[path][method] = op
        return converted

    def write(self) -> None:
        doc = self.generate()
        output_path = Path(self._config.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fmt = self._config.output_format
        if fmt in ("json", "both"):
            json_path = output_path.with_suffix(".json") if fmt == "both" else output_path
            json_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")

        if fmt in ("yaml", "both"):
            try:
                import yaml
            except ImportError as e:
                raise ImportError(
                    "PyYAML is required for YAML output. "
                    "Install it with: pip install pytest-swag[yaml]"
                ) from e
            yaml_path = output_path.with_suffix(".yaml") if fmt == "both" else output_path
            yaml_path.write_text(
                yaml.dump(doc, default_flow_style=False, allow_unicode=True, sort_keys=False)
            )

    def to_stdout(self) -> str:
        doc = self.generate()
        return json.dumps(doc, indent=2, ensure_ascii=False)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_generator.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/pytest_swag/generator.py tests/unit/test_generator.py
git commit -m "feat: add SwagGenerator with JSON/YAML output and component schemas"
```

---

### Task 8: Plugin — pytest Integration

**Files:**
- Create: `src/pytest_swag/plugin.py`
- Update: `src/pytest_swag/__init__.py`
- Create: `tests/integration/test_plugin.py`

- [ ] **Step 1: Write failing integration tests for the plugin**

`tests/integration/test_plugin.py`:

```python
import json


def test_swag_fixture_available(pytester):
    pytester.makepyfile("""
        def test_has_swag(swag):
            assert swag is not None
    """)
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_swag_generates_openapi_json(pytester, tmp_path):
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "openapi": "3.1.0",
                "info": {{"title": "Test API", "version": "1.0.0"}},
                "output_path": "{output}",
                "output_format": "json",
            }}
    """)
    pytester.makepyfile("""
        def test_get_blogs(swag):
            swag.path("/blogs").get("List blogs")
            swag.response(200, description="OK", schema={
                "type": "array",
                "items": {"type": "object"},
            })
            swag.validate(200, [{"id": 1}])
    """)
    result = pytester.runpytest("--swag")
    result.assert_outcomes(passed=1)
    assert output.exists()
    data = json.loads(output.read_text())
    assert data["openapi"] == "3.1.0"
    assert "/blogs" in data["paths"]


def test_no_output_without_swag_flag(pytester, tmp_path):
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "output_path": "{output}",
            }}
    """)
    pytester.makepyfile("""
        def test_get_blogs(swag):
            swag.path("/blogs").get("List blogs")
            swag.response(200, schema={"type": "array"})
            swag.validate(200, [])
    """)
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
    assert not output.exists()


def test_validation_failure_fails_test(pytester):
    pytester.makepyfile("""
        def test_wrong_type(swag):
            swag.path("/blogs").get("List blogs")
            swag.response(200, schema={
                "type": "object",
                "required": ["id"],
                "properties": {"id": {"type": "integer"}},
            })
            swag.validate(200, {"id": "not_an_int"})
    """)
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*SwagValidationError*"])


def test_undocumented_status_code_fails_test(pytester):
    pytester.makepyfile("""
        def test_undocumented(swag):
            swag.path("/blogs").get("List blogs")
            swag.response(200, schema={"type": "array"})
            swag.validate(404, {})
    """)
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*Undocumented status code*"])


def test_failed_test_excluded_from_output(pytester, tmp_path):
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "output_path": "{output}",
            }}
    """)
    pytester.makepyfile("""
        def test_valid(swag):
            swag.path("/valid").get("Valid endpoint")
            swag.response(200, schema={"type": "object"})
            swag.validate(200, {})

        def test_invalid(swag):
            swag.path("/invalid").get("Invalid endpoint")
            swag.response(200, schema={"type": "object", "required": ["id"], "properties": {"id": {"type": "integer"}}})
            swag.validate(200, {"id": "wrong"})
    """)
    result = pytester.runpytest("--swag")
    result.assert_outcomes(passed=1, failed=1)
    data = json.loads(output.read_text())
    assert "/valid" in data["paths"]
    assert "/invalid" not in data["paths"]


def test_ref_schema_validation(pytester, tmp_path):
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "output_path": "{output}",
            }}

        @pytest.fixture(scope="session")
        def swag_schemas():
            return {{
                "Blog": {{
                    "type": "object",
                    "required": ["id"],
                    "properties": {{"id": {{"type": "integer"}}}},
                }}
            }}
    """)
    pytester.makepyfile("""
        def test_get_blog(swag):
            swag.path("/blogs/{id}").get("Get blog")
            swag.parameter("id", in_="path", schema={"type": "string"})
            swag.response(200, schema={"$ref": "#/components/schemas/Blog"})
            swag.validate(200, {"id": 1})
    """)
    result = pytester.runpytest("--swag")
    result.assert_outcomes(passed=1)
    data = json.loads(output.read_text())
    assert data["components"]["schemas"]["Blog"]["type"] == "object"


def test_security_scheme_in_output(pytester, tmp_path):
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "output_path": "{output}",
            }}

        @pytest.fixture(scope="session")
        def swag_security_schemes():
            return {{
                "BearerAuth": {{
                    "type": "http",
                    "scheme": "bearer",
                }}
            }}
    """)
    pytester.makepyfile("""
        def test_secured(swag):
            swag.path("/admin").get("Admin")
            swag.security("BearerAuth")
            swag.response(200, schema={"type": "object"})
            swag.validate(200, {})
    """)
    result = pytester.runpytest("--swag")
    result.assert_outcomes(passed=1)
    data = json.loads(output.read_text())
    assert "BearerAuth" in data["components"]["securitySchemes"]


def test_dry_run_outputs_to_stdout(pytester):
    pytester.makepyfile("""
        def test_blog(swag):
            swag.path("/blogs").get("List")
            swag.response(200, schema={"type": "array"})
            swag.validate(200, [])
    """)
    result = pytester.runpytest("--swag", "--swag-dry-run")
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(['"openapi"*'])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/integration/test_plugin.py -v`
Expected: FAIL — `fixture 'swag' not found`

- [ ] **Step 3: Implement the plugin**

`src/pytest_swag/plugin.py`:

```python
from __future__ import annotations

import pytest

from pytest_swag.builder import SwagBuilder
from pytest_swag.collector import SwagCollector
from pytest_swag.config import SwagConfig
from pytest_swag.generator import SwagGenerator
from pytest_swag.validator import SwagValidator, SwagValidationError


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("swag", "OpenAPI documentation generation")
    group.addoption("--swag", action="store_true", default=False, help="Generate OpenAPI documentation")
    group.addoption("--swag-output", default=None, help="Override output path")
    group.addoption("--swag-no-output", action="store_true", default=False, help="Skip file output")
    group.addoption("--swag-dry-run", action="store_true", default=False, help="Print OpenAPI doc to stdout")
    group.addoption("--swag-strict", action="store_true", default=False, help="Warn on unvalidated tests")


_collector = SwagCollector()


@pytest.fixture(scope="session")
def swag_config() -> dict | list[dict]:
    return {}


@pytest.fixture(scope="session")
def swag_schemas() -> dict:
    return {}


@pytest.fixture(scope="session")
def swag_security_schemes() -> dict:
    return {}


@pytest.fixture
def swag(request, swag_schemas):
    builder = SwagBuilder()
    yield builder
    if not builder._validated:
        if request.config.getoption("--swag-strict", default=False):
            import warnings
            warnings.warn(
                f"Test {request.node.nodeid} uses swag fixture but never called validate()",
                stacklevel=2,
            )
        return
    op = builder.to_operation_dict()
    if builder._doc_target is not None:
        op["doc_target"] = builder._doc_target
    _collector.collect(op)


def _make_validate(builder: SwagBuilder, component_schemas: dict):
    original_validate = None

    def validate(status_code: int, body: object = None) -> None:
        validator = SwagValidator(
            responses=builder._responses,
            path=builder._path,
            method=builder._method,
            component_schemas=component_schemas,
        )
        validator.validate(status_code, body)
        builder._validated = True

    return validate


@pytest.fixture
def swag(request, swag_schemas):
    builder = SwagBuilder()
    component_schemas = swag_schemas
    builder.validate = _make_validate(builder, component_schemas)
    yield builder
    if not builder._validated:
        if request.config.getoption("--swag-strict", default=False):
            import warnings
            warnings.warn(
                f"Test {request.node.nodeid} uses swag fixture but never called validate()",
                stacklevel=2,
            )
        return
    op = builder.to_operation_dict()
    if builder._doc_target is not None:
        op["doc_target"] = builder._doc_target
    _collector.collect(op)


def pytest_configure(config: pytest.Config) -> None:
    global _collector
    _collector = SwagCollector()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    config = session.config
    if not config.getoption("--swag", default=False):
        return

    raw_config = {}
    for item in session.items:
        for fixture_def in item._fixtureinfo.name2fixturedefs.get("swag_config", []):
            if fixture_def.cached_result is not None:
                raw_config = fixture_def.cached_result[0]
                break
        if raw_config:
            break

    raw_schemas = {}
    for item in session.items:
        for fixture_def in item._fixtureinfo.name2fixturedefs.get("swag_schemas", []):
            if fixture_def.cached_result is not None:
                raw_schemas = fixture_def.cached_result[0]
                break
        if raw_schemas:
            break

    raw_security = {}
    for item in session.items:
        for fixture_def in item._fixtureinfo.name2fixturedefs.get("swag_security_schemes", []):
            if fixture_def.cached_result is not None:
                raw_security = fixture_def.cached_result[0]
                break
        if raw_security:
            break

    if config.getoption("--swag-no-output", default=False):
        return

    if isinstance(raw_config, list):
        configs = SwagConfig.from_list(raw_config)
    else:
        configs = [SwagConfig.from_dict(raw_config)]

    output_override = config.getoption("--swag-output", default=None)
    dry_run = config.getoption("--swag-dry-run", default=False)

    for swag_config in configs:
        if output_override and len(configs) == 1:
            swag_config.output_path = output_override

        doc_target = swag_config.info.get("title") if len(configs) > 1 else None
        paths = _collector.merge_to_paths(doc_target=doc_target)

        gen = SwagGenerator(
            config=swag_config,
            paths=paths,
            component_schemas=raw_schemas,
            security_schemes=raw_security,
        )

        if dry_run:
            print(gen.to_stdout())
        else:
            gen.write()
```

- [ ] **Step 4: Remove the duplicate `swag` fixture — keep only the second definition**

The file above has two `swag` fixture definitions. Remove the first one (the simpler version without `validate`). The second definition (with `_make_validate`) is the correct one.

- [ ] **Step 5: Update `__init__.py` with public exports**

`src/pytest_swag/__init__.py`:

```python
"""pytest-swag: Generate OpenAPI documentation from pytest tests."""

__version__ = "0.1.0"

from pytest_swag.builder import SwagBuilder
from pytest_swag.validator import SwagValidationError

__all__ = ["SwagBuilder", "SwagValidationError"]
```

- [ ] **Step 6: Run integration tests to verify they pass**

Run: `pytest tests/integration/test_plugin.py -v`
Expected: All PASS

- [ ] **Step 7: Run all tests to verify nothing is broken**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add src/pytest_swag/plugin.py src/pytest_swag/__init__.py tests/integration/test_plugin.py
git commit -m "feat: add pytest plugin with fixture, CLI options, and session hooks"
```

---

### Task 9: Full E2E Flow Test

**Files:**
- Create: `tests/integration/test_full_flow.py`

- [ ] **Step 1: Write E2E test**

`tests/integration/test_full_flow.py`:

```python
import json


def test_complete_api_documentation(pytester, tmp_path):
    """Full flow: multiple endpoints, schemas, security, tags → single OpenAPI doc."""
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "openapi": "3.1.0",
                "info": {{"title": "Blog API", "version": "1.0.0", "description": "A blog API"}},
                "servers": [{{"url": "https://api.example.com/v1"}}],
                "security": [{{"BearerAuth": []}}],
                "output_path": "{output}",
            }}

        @pytest.fixture(scope="session")
        def swag_schemas():
            return {{
                "Blog": {{
                    "type": "object",
                    "required": ["id", "title"],
                    "properties": {{
                        "id": {{"type": "integer"}},
                        "title": {{"type": "string"}},
                        "content": {{"type": "string"}},
                    }},
                }},
                "Error": {{
                    "type": "object",
                    "properties": {{
                        "message": {{"type": "string"}},
                    }},
                }},
            }}

        @pytest.fixture(scope="session")
        def swag_security_schemes():
            return {{
                "BearerAuth": {{
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }},
            }}
    """)
    pytester.makepyfile("""
        def test_list_blogs(swag):
            swag.path("/blogs").get("List all blogs")
            swag.tag("Blogs")
            swag.parameter("page", in_="query", schema={"type": "integer"})
            swag.response(200, description="OK", schema={
                "type": "array",
                "items": {"$ref": "#/components/schemas/Blog"},
            })
            swag.validate(200, [{"id": 1, "title": "Hello"}])

        def test_get_blog(swag):
            swag.path("/blogs/{id}").get("Get a blog")
            swag.tag("Blogs")
            swag.parameter("id", in_="path", schema={"type": "integer"})
            swag.response(200, schema={"$ref": "#/components/schemas/Blog"})
            swag.response(404, schema={"$ref": "#/components/schemas/Error"})
            swag.validate(200, {"id": 1, "title": "Hello"})

        def test_create_blog(swag):
            swag.path("/blogs").post("Create a blog")
            swag.tag("Blogs")
            swag.request_body(
                content_type="application/json",
                schema={
                    "type": "object",
                    "required": ["title"],
                    "properties": {"title": {"type": "string"}, "content": {"type": "string"}},
                },
            )
            swag.response(201, schema={"$ref": "#/components/schemas/Blog"})
            swag.validate(201, {"id": 2, "title": "New Blog"})

        def test_delete_blog(swag):
            swag.path("/blogs/{id}").delete("Delete a blog")
            swag.tag("Blogs")
            swag.parameter("id", in_="path", schema={"type": "integer"})
            swag.response(204, description="Deleted")
            swag.validate(204, None)
    """)
    result = pytester.runpytest("--swag", "-v")
    result.assert_outcomes(passed=4)

    assert output.exists()
    doc = json.loads(output.read_text())

    # Structure checks
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "Blog API"
    assert doc["servers"][0]["url"] == "https://api.example.com/v1"
    assert doc["security"] == [{"BearerAuth": []}]

    # Paths
    assert "/blogs" in doc["paths"]
    assert "get" in doc["paths"]["/blogs"]
    assert "post" in doc["paths"]["/blogs"]
    assert "/blogs/{id}" in doc["paths"]
    assert "get" in doc["paths"]["/blogs/{id}"]
    assert "delete" in doc["paths"]["/blogs/{id}"]

    # Components
    assert "Blog" in doc["components"]["schemas"]
    assert "Error" in doc["components"]["schemas"]
    assert "BearerAuth" in doc["components"]["securitySchemes"]

    # Tags
    assert doc["paths"]["/blogs"]["get"]["tags"] == ["Blogs"]


def test_multi_doc_output(pytester, tmp_path):
    """Multiple OpenAPI documents from a single test suite."""
    v1_output = tmp_path / "v1.json"
    v2_output = tmp_path / "v2.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return [
                {{"info": {{"title": "API v1", "version": "1.0.0"}}, "output_path": "{v1_output}"}},
                {{"info": {{"title": "API v2", "version": "2.0.0"}}, "output_path": "{v2_output}"}},
            ]
    """)
    pytester.makepyfile("""
        def test_v1_endpoint(swag):
            swag.doc("API v1")
            swag.path("/v1/blogs").get("List v1")
            swag.response(200, schema={"type": "array"})
            swag.validate(200, [])

        def test_v2_endpoint(swag):
            swag.doc("API v2")
            swag.path("/v2/blogs").get("List v2")
            swag.response(200, schema={"type": "array"})
            swag.validate(200, [])
    """)
    result = pytester.runpytest("--swag", "-v")
    result.assert_outcomes(passed=2)

    v1 = json.loads(v1_output.read_text())
    v2 = json.loads(v2_output.read_text())
    assert "/v1/blogs" in v1["paths"]
    assert "/v1/blogs" not in v2.get("paths", {})
    assert "/v2/blogs" in v2["paths"]
    assert "/v2/blogs" not in v1.get("paths", {})
```

- [ ] **Step 2: Run E2E tests**

Run: `pytest tests/integration/test_full_flow.py -v`
Expected: All PASS

- [ ] **Step 3: Run full test suite**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_full_flow.py
git commit -m "test: add full E2E flow tests for multi-endpoint and multi-doc scenarios"
```

---

### Task 10: Polish and Final Verification

**Files:**
- Modify: `src/pytest_swag/__init__.py`
- Verify: all tests pass, plugin installs cleanly

- [ ] **Step 1: Verify clean install in fresh venv**

```bash
cd /Users/jwshin/Desktop/develop/workspace/builder-shin/library/python/pytest-swag
python -m venv /tmp/test-swag-venv && source /tmp/test-swag-venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
deactivate && rm -rf /tmp/test-swag-venv
```

Expected: All tests pass in clean environment

- [ ] **Step 2: Verify plugin auto-discovery**

```bash
pytest --co -p pytest_swag.plugin 2>&1 | head -5
```

Expected: No errors, plugin loads

- [ ] **Step 3: Run ruff for linting**

```bash
ruff check src/ tests/
```

Expected: No issues (fix any if found)

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: polish and verify clean install"
```

---

### Task 11: Requests Adapter

HTTP 클라이언트 자동 연동 어댑터. `pip install pytest-swag[requests]`로 설치하면 `swag.validate_response(response)`로 requests.Response 객체를 직접 전달할 수 있다.

**Files:**
- Create: `src/pytest_swag/adapters/__init__.py`
- Create: `src/pytest_swag/adapters/requests.py`
- Create: `tests/unit/test_adapter_requests.py`

- [ ] **Step 1: Write failing tests for requests adapter**

`tests/unit/test_adapter_requests.py`:

```python
import pytest
from unittest.mock import MagicMock
from pytest_swag.adapters.requests import validate_response, RequestsSwagBuilder
from pytest_swag.validator import SwagValidationError


class TestValidateResponse:
    def _make_response(self, status_code: int, json_data: object = None) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        resp.headers = {"Content-Type": "application/json"}
        return resp

    def test_valid_response(self):
        responses = {200: {"description": "OK", "schema": {"type": "object", "properties": {"id": {"type": "integer"}}}}}
        resp = self._make_response(200, {"id": 1})
        validate_response(resp, responses=responses, path="/blogs", method="get")

    def test_invalid_response_raises(self):
        responses = {200: {"description": "OK", "schema": {"type": "object", "required": ["id"], "properties": {"id": {"type": "integer"}}}}}
        resp = self._make_response(200, {"id": "wrong"})
        with pytest.raises(SwagValidationError):
            validate_response(resp, responses=responses, path="/blogs", method="get")

    def test_no_content_type_skips_json_parse(self):
        responses = {204: {"description": "No content", "schema": None}}
        resp = self._make_response(204, None)
        resp.headers = {}
        validate_response(resp, responses=responses, path="/blogs/{id}", method="delete")


class TestRequestsSwagBuilder:
    def _make_response(self, status_code: int, json_data: object = None) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        resp.headers = {"Content-Type": "application/json"}
        return resp

    def test_validate_response_method(self):
        b = RequestsSwagBuilder()
        b.path("/blogs").get("List blogs")
        b.response(200, schema={"type": "array", "items": {"type": "object"}})
        resp = self._make_response(200, [{"id": 1}])
        b.validate_response(resp)
        assert b._validated is True

    def test_validate_response_fails_on_wrong_schema(self):
        b = RequestsSwagBuilder()
        b.path("/blogs").get("List blogs")
        b.response(200, schema={"type": "object", "required": ["id"], "properties": {"id": {"type": "integer"}}})
        resp = self._make_response(200, {"id": "not_int"})
        with pytest.raises(SwagValidationError):
            b.validate_response(resp)

    def test_validate_response_extracts_body_from_json(self):
        b = RequestsSwagBuilder()
        b.path("/blogs").get("List")
        b.response(200, schema={"type": "object", "properties": {"name": {"type": "string"}}})
        resp = self._make_response(200, {"name": "hello"})
        b.validate_response(resp)  # should not raise

    def test_validate_response_no_body_for_204(self):
        b = RequestsSwagBuilder()
        b.path("/blogs/{id}").delete("Delete")
        b.response(204, description="Deleted")
        resp = self._make_response(204, None)
        resp.headers = {}
        b.validate_response(resp)
        assert b._validated is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_adapter_requests.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pytest_swag.adapters'`

- [ ] **Step 3: Create adapters __init__.py**

`src/pytest_swag/adapters/__init__.py`:

```python
"""HTTP client adapters for pytest-swag."""
```

- [ ] **Step 4: Implement requests adapter**

`src/pytest_swag/adapters/requests.py`:

```python
from __future__ import annotations

from pytest_swag.builder import SwagBuilder
from pytest_swag.validator import SwagValidator


def _extract_body(response: object) -> object | None:
    content_type = getattr(response, "headers", {}).get("Content-Type", "")
    if "application/json" not in content_type:
        return None
    try:
        return response.json()
    except Exception:
        return None


def validate_response(
    response: object,
    *,
    responses: dict[int, dict],
    path: str,
    method: str,
    component_schemas: dict | None = None,
) -> None:
    validator = SwagValidator(
        responses=responses,
        path=path,
        method=method,
        component_schemas=component_schemas,
    )
    body = _extract_body(response)
    validator.validate(response.status_code, body)


class RequestsSwagBuilder(SwagBuilder):
    def validate_response(
        self,
        response: object,
        *,
        component_schemas: dict | None = None,
    ) -> None:
        body = _extract_body(response)
        validator = SwagValidator(
            responses=self._responses,
            path=self._path,
            method=self._method,
            component_schemas=component_schemas or {},
        )
        validator.validate(response.status_code, body)
        self._validated = True
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/test_adapter_requests.py -v`
Expected: All PASS

- [ ] **Step 6: Add `swag_requests` fixture to plugin**

Add the following to `src/pytest_swag/plugin.py`, after the existing `swag` fixture:

```python
@pytest.fixture
def swag_requests(request, swag_schemas):
    from pytest_swag.adapters.requests import RequestsSwagBuilder
    builder = RequestsSwagBuilder()
    builder.validate = _make_validate(builder, swag_schemas)

    def _validate_response(response, *, component_schemas=None):
        builder.validate_response(response, component_schemas=component_schemas or swag_schemas)

    builder.validate_response = _validate_response
    yield builder
    if not builder._validated:
        if request.config.getoption("--swag-strict", default=False):
            import warnings
            warnings.warn(
                f"Test {request.node.nodeid} uses swag_requests fixture but never called validate_response()",
                stacklevel=2,
            )
        return
    op = builder.to_operation_dict()
    if builder._doc_target is not None:
        op["doc_target"] = builder._doc_target
    _collector.collect(op)
```

- [ ] **Step 7: Write integration test for swag_requests fixture**

Add to `tests/integration/test_full_flow.py`:

```python
def test_requests_adapter_flow(pytester, tmp_path):
    """requests adapter: validate_response() auto-extracts status_code and body."""
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "output_path": "{output}",
            }}
    """)
    pytester.makepyfile("""
        from unittest.mock import MagicMock

        def _mock_response(status_code, json_data):
            resp = MagicMock()
            resp.status_code = status_code
            resp.json.return_value = json_data
            resp.headers = {"Content-Type": "application/json"}
            return resp

        def test_with_requests_adapter(swag_requests):
            swag_requests.path("/blogs").get("List blogs")
            swag_requests.response(200, schema={{
                "type": "array",
                "items": {{"type": "object", "properties": {{"id": {{"type": "integer"}}}}}},
            }})
            resp = _mock_response(200, [{{"id": 1}}])
            swag_requests.validate_response(resp)
    """)
    result = pytester.runpytest("--swag", "-v")
    result.assert_outcomes(passed=1)
    assert output.exists()
    data = __import__("json").loads(output.read_text())
    assert "/blogs" in data["paths"]
```

- [ ] **Step 8: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 9: Commit**

```bash
git add src/pytest_swag/adapters/ tests/unit/test_adapter_requests.py
git add -u src/pytest_swag/plugin.py tests/integration/test_full_flow.py
git commit -m "feat: add requests adapter with swag_requests fixture and validate_response()"
```
