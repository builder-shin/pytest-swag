from pytest_swag.adapters.jsonapi.mixin import JsonApiMixin, JsonApiSwagBuilder
from pytest_swag.adapters.jsonapi.resource import (
    JsonApiResource,
    JsonApiRelationship,
)


class TestJsonApiResourceMethod:
    def test_sets_jsonapi_body(self):
        b = JsonApiSwagBuilder()
        b.jsonapi_resource("articles", attributes={"title": "Hello"})
        assert b._jsonapi_body is not None
        assert b._jsonapi_body.type == "articles"
        assert b._jsonapi_body.attributes == {"title": "Hello"}

    def test_returns_self_for_chaining(self):
        b = JsonApiSwagBuilder()
        result = b.jsonapi_resource("articles")
        assert result is b

    def test_with_id(self):
        b = JsonApiSwagBuilder()
        b.jsonapi_resource("articles", id="1", attributes={"title": "Hi"})
        assert b._jsonapi_body.id == "1"


class TestJsonApiRelationshipMethod:
    def test_adds_to_one_relationship(self):
        b = JsonApiSwagBuilder()
        b.jsonapi_resource("articles", attributes={"title": "Hi"})
        b.jsonapi_relationship("author", type="people", id="1")
        rels = b._jsonapi_body.relationships
        assert rels["author"].data.type == "people"
        assert rels["author"].data.id == "1"

    def test_adds_multiple_relationships(self):
        b = JsonApiSwagBuilder()
        b.jsonapi_resource("articles")
        b.jsonapi_relationship("author", type="people", id="1")
        b.jsonapi_relationship("reviewer", type="people", id="2")
        rels = b._jsonapi_body.relationships
        assert "author" in rels
        assert "reviewer" in rels

    def test_returns_self_for_chaining(self):
        b = JsonApiSwagBuilder()
        b.jsonapi_resource("articles")
        result = b.jsonapi_relationship("author", type="people", id="1")
        assert result is b


class TestJsonApiRelationshipsMethod:
    def test_adds_to_many_relationship(self):
        b = JsonApiSwagBuilder()
        b.jsonapi_resource("articles")
        b.jsonapi_relationships("tags", items=[("tags", "1"), ("tags", "2")])
        rels = b._jsonapi_body.relationships
        assert len(rels["tags"].data) == 2


class TestJsonApiBodyMethod:
    def test_sets_pre_built_resource(self):
        b = JsonApiSwagBuilder()
        resource = JsonApiResource(
            type="articles",
            attributes={"title": "Hello"},
            relationships={
                "author": JsonApiRelationship.to_one("people", "1"),
            },
        )
        b.jsonapi_body(resource)
        assert b._jsonapi_body is resource

    def test_returns_self_for_chaining(self):
        b = JsonApiSwagBuilder()
        result = b.jsonapi_body(JsonApiResource(type="articles"))
        assert result is b


class TestJsonApiMetaMethod:
    def test_sets_top_level_meta(self):
        b = JsonApiSwagBuilder()
        b.jsonapi_meta({"request_id": "abc"})
        assert b._jsonapi_meta == {"request_id": "abc"}

    def test_returns_self_for_chaining(self):
        b = JsonApiSwagBuilder()
        result = b.jsonapi_meta({"key": "value"})
        assert result is b


class TestJsonApiResponse:
    def test_delegates_to_parent_response(self):
        b = JsonApiSwagBuilder()
        b.path("/articles").get()
        b.jsonapi_response(200, resource_type="articles")
        assert 200 in b._responses

    def test_response_schema_uses_jsonapi_envelope(self):
        b = JsonApiSwagBuilder()
        b.path("/articles").get()
        b.jsonapi_response(200, resource_type="articles")
        schema = b._responses[200]["schema"]
        assert "properties" in schema
        assert "data" in schema["properties"]

    def test_collection_response(self):
        b = JsonApiSwagBuilder()
        b.path("/articles").get()
        b.jsonapi_response(200, resource_type="articles", is_collection=True)
        schema = b._responses[200]["schema"]
        data = schema["properties"]["data"]
        assert data["type"] == "array"

    def test_returns_self_for_chaining(self):
        b = JsonApiSwagBuilder()
        b.path("/articles").get()
        result = b.jsonapi_response(200, resource_type="articles")
        assert result is b


class TestJsonApiErrorResponse:
    def test_delegates_error_response(self):
        b = JsonApiSwagBuilder()
        b.path("/articles").post()
        b.jsonapi_error_response(422)
        assert 422 in b._responses
        schema = b._responses[422]["schema"]
        assert "errors" in schema["properties"]

    def test_returns_self_for_chaining(self):
        b = JsonApiSwagBuilder()
        b.path("/articles").post()
        result = b.jsonapi_error_response(422)
        assert result is b


class TestHeaderAutomation:
    def test_apply_headers_sets_accept(self):
        b = JsonApiSwagBuilder()
        b.path("/articles").post()
        b._apply_jsonapi_headers()
        header_params = [p for p in b._parameters if p["in"] == "header"]
        accept = [p for p in header_params if p["name"] == "Accept"]
        assert len(accept) == 1
        assert accept[0]["value"] == "application/vnd.api+json"

    def test_apply_headers_does_not_overwrite_manual(self):
        b = JsonApiSwagBuilder()
        b.path("/articles").post()
        b.jsonapi_content_type("application/json")
        b._apply_jsonapi_headers()
        assert b._jsonapi_content_type_overridden is True

    def test_jsonapi_content_type_override(self):
        b = JsonApiSwagBuilder()
        result = b.jsonapi_content_type("application/json")
        assert result is b
        assert b._jsonapi_content_type_overridden is True


class TestToOperationDict:
    def test_adds_x_jsonapi_marker(self):
        b = JsonApiSwagBuilder()
        b.path("/articles").get()
        b.jsonapi_response(200, resource_type="articles")
        op = b.to_operation_dict()
        assert op.get("x-jsonapi") is True

    def test_jsonapi_request_body_in_operation(self):
        b = JsonApiSwagBuilder()
        b.path("/articles").post()
        b.jsonapi_resource("articles", attributes={"title": "Hi"})
        b.jsonapi_response(201, resource_type="articles")
        op = b.to_operation_dict()
        rb = op["requestBody"]
        assert "application/vnd.api+json" in rb["content"]

    def test_jsonapi_response_content_type_in_operation(self):
        b = JsonApiSwagBuilder()
        b.path("/articles").get()
        b.jsonapi_response(200, resource_type="articles")
        op = b.to_operation_dict()
        resp = op["responses"][200]
        assert "application/vnd.api+json" in resp["content"]

    def test_no_jsonapi_marker_without_jsonapi_methods(self):
        b = JsonApiSwagBuilder()
        b.path("/articles").get()
        b.response(200, schema={"type": "object"})
        op = b.to_operation_dict()
        assert "x-jsonapi" not in op
