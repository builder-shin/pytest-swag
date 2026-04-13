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
