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
