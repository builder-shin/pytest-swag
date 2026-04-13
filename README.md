# pytest-swag

Generate OpenAPI documentation from pytest tests.

pytest-swag is a **framework-agnostic** pytest plugin that turns your existing API tests into living OpenAPI 3.0/3.1 documentation. Define your API spec inline with a fluent builder DSL, validate responses against it with jsonschema, and produce a complete OpenAPI document at the end of your test session.

---

**English | [한국어](README.ko.md)**

---

### Installation

```bash
pip install pytest-swag
```

Optional extras:

```bash
pip install pytest-swag[yaml]       # YAML output support
pip install pytest-swag[requests]   # requests library adapter
pip install pytest-swag[dev]        # Development dependencies
```

### Quick Start

```python
def test_get_blog(swag):
    swag.path("/blogs/{id}").get("Retrieves a blog")
    swag.parameter("id", in_="path", schema={"type": "string"})
    swag.response(200, schema={
        "type": "object",
        "properties": {"id": {"type": "integer"}, "title": {"type": "string"}},
    })

    response = client.get("/blogs/1")
    swag.validate(response.status_code, response.json())
```

Run your tests with the `--swag` flag:

```bash
pytest --swag
```

This generates an `openapi.json` file containing your full API specification.

### How It Works

1. **Define** your API spec using the `swag` fixture's builder DSL
2. **Validate** each response against the declared schema (jsonschema)
3. **Collect** all validated operations across your test suite
4. **Generate** a complete OpenAPI document at session end

Only tests that pass validation are included in the output. Failed tests are automatically excluded, keeping your documentation accurate.

### Configuration

#### Via `pyproject.toml`

```toml
[tool.pytest-swag]
openapi = "3.1.0"
output_path = "docs/openapi.json"
output_format = "json"   # "json", "yaml", or "both"

[tool.pytest-swag.info]
title = "My API"
version = "1.0.0"
```

#### Via `conftest.py` fixture

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

### Builder DSL Reference

#### Path & HTTP Methods

```python
swag.path("/users").get("List users")
swag.path("/users").post("Create user")
swag.path("/users/{id}").put("Update user")
swag.path("/users/{id}").patch("Partial update")
swag.path("/users/{id}").delete("Delete user")
```

#### Parameters

```python
# Path parameter (always required)
swag.parameter("id", in_="path", schema={"type": "integer"})

# Query parameter (optional by default)
swag.parameter("page", in_="query", schema={"type": "integer"})

# Required header
swag.parameter("X-Api-Key", in_="header", schema={"type": "string"}, required=True)
```

#### Request Body

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

#### Responses

```python
# With schema
swag.response(200, description="OK", schema={
    "type": "object",
    "properties": {"id": {"type": "integer"}},
})

# Without schema (e.g. 204 No Content)
swag.response(204, description="Deleted")

# With $ref (requires swag_schemas fixture)
swag.response(200, schema={"$ref": "#/components/schemas/User"})
```

#### Tags & Security

```python
swag.tag("Users")
swag.security("BearerAuth")
```

#### Validation

```python
# Manual validation
swag.validate(response.status_code, response.json())

# Validates:
# 1. Status code is documented
# 2. Response body matches the declared schema (via jsonschema)
```

#### Capture (Schema-Free)

Record actual API responses for documentation without defining schemas upfront.
Schemas are automatically inferred from the response body.

```python
def test_get_blog(swag):
    swag.path("/blogs/{id}").get("Get blog")
    swag.parameter("id", in_="path", schema={"type": "string"})

    response = client.get("/blogs/1")
    assert response.status_code == 200       # validate with pytest
    assert "title" in response.json()

    swag.capture(200, response.json())       # capture for docs

# Disable schema inference (example only)
    swag.capture(200, response.json(), infer_schema=False)
```

The `swag_requests` fixture auto-captures on `validate_response()`.

> **Note:** `capture()` and `validate()` cannot be used in the same test.

### Component Schemas (`$ref` Support)

Define reusable schemas via the `swag_schemas` fixture:

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

Then reference them in your tests:

```python
def test_get_user(swag):
    swag.path("/users/{id}").get("Get user")
    swag.parameter("id", in_="path", schema={"type": "integer"})
    swag.response(200, schema={"$ref": "#/components/schemas/User"})
    swag.response(404, schema={"$ref": "#/components/schemas/Error"})

    response = client.get("/users/1")
    swag.validate(response.status_code, response.json())
```

The `$ref` references are recursively resolved during validation and preserved as-is in the generated OpenAPI document.

### Security Schemes

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

### Requests Adapter

For projects using the `requests` library, use the `swag_requests` fixture for automatic response extraction:

```python
def test_list_users(swag_requests):
    swag_requests.path("/users").get("List users")
    swag_requests.response(200, schema={
        "type": "array",
        "items": {"$ref": "#/components/schemas/User"},
    })

    response = requests.get("http://localhost:8000/users")
    swag_requests.validate_response(response)
    # Automatically extracts status_code and JSON body from the response object
```

For schema-free capture without validation:

```python
def test_list_users(swag_requests):
    swag_requests.path("/users").get("List users")

    response = requests.get("http://localhost:8000/users")
    assert response.status_code == 200          # validate with pytest

    swag_requests.capture_response(response)    # capture for docs (schema auto-inferred)
```

### Multi-Document Output

Generate multiple OpenAPI documents from a single test suite using `swag.doc()`:

```python
@pytest.fixture(scope="session")
def swag_config():
    return [
        {"info": {"title": "Public API", "version": "1.0.0"}, "output_path": "docs/public.json"},
        {"info": {"title": "Admin API", "version": "1.0.0"}, "output_path": "docs/admin.json"},
    ]

def test_public_endpoint(swag):
    swag.doc("Public API")
    swag.path("/posts").get("List posts")
    swag.response(200, schema={"type": "array"})
    swag.validate(200, [])

def test_admin_endpoint(swag):
    swag.doc("Admin API")
    swag.path("/admin/users").get("List all users")
    swag.response(200, schema={"type": "array"})
    swag.validate(200, [])
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--swag` | Enable OpenAPI document generation |
| `--swag-output PATH` | Override the output file path |
| `--swag-dry-run` | Print the OpenAPI document to stdout instead of writing a file |
| `--swag-no-output` | Run validation only, skip file generation |
| `--swag-strict` | Warn when a test uses the `swag` fixture but never calls `validate()` |

### Full Example

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
    swag.path("/blogs").get("List all blogs")
    swag.tag("Blogs")
    swag.parameter("page", in_="query", schema={"type": "integer"})
    swag.response(200, schema={
        "type": "array",
        "items": {"$ref": "#/components/schemas/Blog"},
    })

    response = client.get("/blogs")
    swag.validate(response.status_code, response.json())

def test_create_blog(swag):
    swag.path("/blogs").post("Create a blog")
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
    swag.path("/blogs/{id}").delete("Delete a blog")
    swag.tag("Blogs")
    swag.parameter("id", in_="path", schema={"type": "integer"})
    swag.response(204, description="Deleted")

    response = client.delete("/blogs/1")
    swag.validate(response.status_code, None)
```

```bash
pytest --swag
# Generates docs/openapi.json and docs/openapi.yaml
```

### Requirements

- Python >= 3.10
- pytest >= 7.0
- jsonschema >= 4.0
- PyYAML >= 6.0 (optional, for YAML output)

### Acknowledgments

pytest-swag is inspired by [rswag](https://github.com/rswag/rswag), the excellent Ruby/RSpec library for generating Swagger/OpenAPI documentation from integration tests. We are grateful to the rswag team for pioneering the "test-driven documentation" approach that bridges the gap between API testing and API documentation. pytest-swag brings this philosophy to the Python/pytest ecosystem.

### License

MIT
