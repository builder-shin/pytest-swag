import pytest
from pytest_swag.builder import SwagBuilder, SwagBuildError


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

    def test_operation_with_capture_includes_example(self):
        b = SwagBuilder()
        b.path("/blogs").get("List blogs")
        b.capture(200, [{"id": 1, "title": "Hello"}])

        op = b.to_operation_dict()
        resp_200 = op["responses"][200]
        content = resp_200["content"]["application/json"]
        assert "schema" in content
        assert content["example"] == [{"id": 1, "title": "Hello"}]

    def test_operation_with_capture_no_schema(self):
        b = SwagBuilder()
        b.path("/blogs").get("List blogs")
        b.capture(200, {"id": 1}, infer_schema=False)

        op = b.to_operation_dict()
        resp_200 = op["responses"][200]
        content = resp_200["content"]["application/json"]
        assert "schema" not in content
        assert content["example"] == {"id": 1}

    def test_operation_with_capture_none_body(self):
        b = SwagBuilder()
        b.path("/blogs/{id}").delete("Delete blog")
        b.capture(204, None)

        op = b.to_operation_dict()
        resp_204 = op["responses"][204]
        assert "content" not in resp_204


class TestCapture:
    def test_capture_stores_response_with_inferred_schema(self):
        b = SwagBuilder()
        b.path("/blogs").get("List blogs")
        b.capture(200, {"id": 1, "title": "Hello"})
        assert 200 in b._responses
        assert b._responses[200]["schema"] == {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string"},
            },
        }
        assert b._responses[200]["example"] == {"id": 1, "title": "Hello"}
        assert b._validated is True

    def test_capture_without_schema_inference(self):
        b = SwagBuilder()
        b.path("/blogs").get("List blogs")
        b.capture(200, {"id": 1}, infer_schema=False)
        assert b._responses[200]["schema"] is None
        assert b._responses[200]["example"] == {"id": 1}

    def test_capture_custom_description(self):
        b = SwagBuilder()
        b.path("/blogs").get("List blogs")
        b.capture(200, [], description="Blog list")
        assert b._responses[200]["description"] == "Blog list"

    def test_capture_default_description(self):
        b = SwagBuilder()
        b.path("/blogs").get("List blogs")
        b.capture(200, [])
        assert b._responses[200]["description"] == "OK"

    def test_capture_none_body(self):
        b = SwagBuilder()
        b.path("/blogs/{id}").delete("Delete blog")
        b.capture(204, None)
        assert b._responses[204]["schema"] is None
        assert b._responses[204]["example"] is None

    def test_capture_sets_validated(self):
        b = SwagBuilder()
        b.path("/blogs").get("List blogs")
        b.capture(200, {"id": 1})
        assert b._validated is True

    def test_capture_after_validate_raises(self):
        b = SwagBuilder()
        b.path("/blogs").get("List blogs")
        b._validated = True
        with pytest.raises(SwagBuildError, match="Cannot mix capture"):
            b.capture(200, {"id": 1})

    def test_capture_multiple_status_codes(self):
        b = SwagBuilder()
        b.path("/blogs/{id}").get("Get blog")
        b.capture(200, {"id": 1})
        b.capture(404, {"message": "Not found"})
        assert 200 in b._responses
        assert 404 in b._responses

    def test_validate_after_capture_raises(self):
        from pytest_swag.plugin import _make_validate

        b = SwagBuilder()
        b.path("/blogs").get("List blogs")
        b.response(200, schema={"type": "object"})
        b.capture(200, {"id": 1})
        validate_fn = _make_validate(b, {})
        with pytest.raises(SwagBuildError, match="Cannot mix capture"):
            validate_fn(200, {"id": 1})
