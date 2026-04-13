from pytest_swag.adapters.jsonapi.resource import (
    JsonApiResource,
    JsonApiRelationship,
)


class TestJsonApiResource:
    def test_minimal_resource(self):
        r = JsonApiResource(type="articles")
        assert r.type == "articles"
        assert r.id is None
        assert r.attributes is None
        assert r.relationships is None
        assert r.links is None
        assert r.meta is None

    def test_full_resource(self):
        r = JsonApiResource(
            type="articles",
            id="1",
            attributes={"title": "Hello"},
            links={"self": "/articles/1"},
            meta={"created": "2026-01-01"},
        )
        assert r.type == "articles"
        assert r.id == "1"
        assert r.attributes == {"title": "Hello"}
        assert r.links == {"self": "/articles/1"}
        assert r.meta == {"created": "2026-01-01"}

    def test_resource_with_relationship(self):
        rel = JsonApiRelationship(
            data=JsonApiResource(type="people", id="5")
        )
        r = JsonApiResource(
            type="articles",
            id="1",
            relationships={"author": rel},
        )
        assert r.relationships["author"].data.type == "people"
        assert r.relationships["author"].data.id == "5"


class TestJsonApiRelationship:
    def test_to_one(self):
        rel = JsonApiRelationship.to_one("people", "1")
        assert rel.data.type == "people"
        assert rel.data.id == "1"

    def test_to_many(self):
        rel = JsonApiRelationship.to_many([("tags", "1"), ("tags", "2")])
        assert len(rel.data) == 2
        assert rel.data[0].type == "tags"
        assert rel.data[0].id == "1"
        assert rel.data[1].id == "2"

    def test_relationship_with_links(self):
        rel = JsonApiRelationship(
            data=JsonApiResource(type="people", id="1"),
            links={"related": "/articles/1/author"},
        )
        assert rel.links == {"related": "/articles/1/author"}

    def test_relationship_with_meta(self):
        rel = JsonApiRelationship(
            data=JsonApiResource(type="people", id="1"),
            meta={"count": 1},
        )
        assert rel.meta == {"count": 1}
