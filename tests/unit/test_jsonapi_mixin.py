from pytest_swag.adapters.jsonapi.mixin import JsonApiSwagBuilder
from pytest_swag.adapters.jsonapi.query import JsonApiQuery
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


class TestJsonApiFieldsMethod:
    def test_sets_fields(self):
        b = JsonApiSwagBuilder()
        b.jsonapi_fields("articles", ["title", "body"])
        assert b._jsonapi_query.fields == {"articles": ["title", "body"]}

    def test_accumulates_fields(self):
        b = JsonApiSwagBuilder()
        b.jsonapi_fields("articles", ["title"])
        b.jsonapi_fields("people", ["name"])
        assert b._jsonapi_query.fields == {
            "articles": ["title"],
            "people": ["name"],
        }

    def test_returns_self_for_chaining(self):
        b = JsonApiSwagBuilder()
        result = b.jsonapi_fields("articles", ["title"])
        assert result is b


class TestJsonApiIncludeMethod:
    def test_sets_include(self):
        b = JsonApiSwagBuilder()
        b.jsonapi_include("author", "comments")
        assert b._jsonapi_query.include == ["author", "comments"]

    def test_accumulates_include(self):
        b = JsonApiSwagBuilder()
        b.jsonapi_include("author")
        b.jsonapi_include("comments.author")
        assert b._jsonapi_query.include == ["author", "comments.author"]

    def test_returns_self_for_chaining(self):
        b = JsonApiSwagBuilder()
        result = b.jsonapi_include("author")
        assert result is b


class TestJsonApiFilterMethod:
    def test_simple_filter(self):
        b = JsonApiSwagBuilder()
        b.jsonapi_filter("status", "published")
        assert b._jsonapi_query.filter == {"status": "published"}

    def test_operator_filter(self):
        b = JsonApiSwagBuilder()
        b.jsonapi_filter("created_at", {"gte": "2026-01-01"})
        assert b._jsonapi_query.filter == {"created_at": {"gte": "2026-01-01"}}

    def test_accumulates_filters(self):
        b = JsonApiSwagBuilder()
        b.jsonapi_filter("status", "published")
        b.jsonapi_filter("author", "1")
        assert b._jsonapi_query.filter == {"status": "published", "author": "1"}

    def test_returns_self_for_chaining(self):
        b = JsonApiSwagBuilder()
        result = b.jsonapi_filter("status", "published")
        assert result is b


class TestJsonApiSortMethod:
    def test_sets_sort(self):
        b = JsonApiSwagBuilder()
        b.jsonapi_sort("-created_at", "title")
        assert b._jsonapi_query.sort == ["-created_at", "title"]

    def test_returns_self_for_chaining(self):
        b = JsonApiSwagBuilder()
        result = b.jsonapi_sort("-created_at")
        assert result is b


class TestJsonApiPageMethod:
    def test_sets_page(self):
        b = JsonApiSwagBuilder()
        b.jsonapi_page(number=1, size=20)
        assert b._jsonapi_query.page == {"number": 1, "size": 20}

    def test_returns_self_for_chaining(self):
        b = JsonApiSwagBuilder()
        result = b.jsonapi_page(number=1, size=10)
        assert result is b


class TestJsonApiQueryMethod:
    def test_sets_pre_built_query(self):
        q = JsonApiQuery(
            include=["author"],
            sort=["-created_at"],
        )
        b = JsonApiSwagBuilder()
        b.jsonapi_query(q)
        assert b._jsonapi_query is q

    def test_returns_self_for_chaining(self):
        b = JsonApiSwagBuilder()
        result = b.jsonapi_query(JsonApiQuery())
        assert result is b


class TestQueryInToOperationDict:
    def test_query_params_become_openapi_parameters(self):
        b = JsonApiSwagBuilder()
        b.path("/articles").get()
        b.jsonapi_fields("articles", ["title"])
        b.jsonapi_include("author")
        b.jsonapi_sort("-created_at")
        b.jsonapi_page(number=1, size=10)
        b.jsonapi_response(200, resource_type="articles", is_collection=True)

        op = b.to_operation_dict()
        param_names = [p["name"] for p in op["parameters"]]
        assert "fields[articles]" in param_names
        assert "include" in param_names
        assert "sort" in param_names
        assert "page[number]" in param_names
        assert "page[size]" in param_names

    def test_query_params_are_optional(self):
        b = JsonApiSwagBuilder()
        b.path("/articles").get()
        b.jsonapi_include("author")
        b.jsonapi_response(200, resource_type="articles", is_collection=True)

        op = b.to_operation_dict()
        include_param = [p for p in op["parameters"] if p["name"] == "include"][0]
        assert include_param["required"] is False
        assert include_param["in"] == "query"

    def test_filter_params_in_openapi(self):
        b = JsonApiSwagBuilder()
        b.path("/articles").get()
        b.jsonapi_filter("status", "published")
        b.jsonapi_filter("created_at", {"gte": "2026-01-01"})
        b.jsonapi_response(200, resource_type="articles", is_collection=True)

        op = b.to_operation_dict()
        param_names = [p["name"] for p in op["parameters"]]
        assert "filter[status]" in param_names
        assert "filter[created_at][gte]" in param_names
