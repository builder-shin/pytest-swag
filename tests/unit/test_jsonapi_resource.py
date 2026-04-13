from pytest_swag.adapters.jsonapi.resource import (
    JsonApiResource,
    JsonApiRelationship,
    JsonApiError,
    JsonApiDocument,
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


class TestJsonApiError:
    def test_minimal_error(self):
        e = JsonApiError(status="422", title="Invalid")
        assert e.status == "422"
        assert e.title == "Invalid"
        assert e.detail is None

    def test_full_error(self):
        e = JsonApiError(
            status="422",
            title="Invalid Attribute",
            detail="Title is required",
            code="VALIDATION_ERROR",
            source={"pointer": "/data/attributes/title"},
            meta={"severity": "high"},
        )
        assert e.source == {"pointer": "/data/attributes/title"}
        assert e.code == "VALIDATION_ERROR"
        assert e.meta == {"severity": "high"}


class TestJsonApiDocument:
    def test_single_resource_document(self):
        doc = JsonApiDocument(
            data=JsonApiResource(type="articles", id="1", attributes={"title": "Hi"})
        )
        assert doc.data.type == "articles"
        assert doc.errors is None

    def test_collection_document(self):
        doc = JsonApiDocument(
            data=[
                JsonApiResource(type="articles", id="1"),
                JsonApiResource(type="articles", id="2"),
            ]
        )
        assert len(doc.data) == 2

    def test_error_document(self):
        doc = JsonApiDocument(
            errors=[JsonApiError(status="404", title="Not Found")]
        )
        assert doc.data is None
        assert len(doc.errors) == 1

    def test_document_with_meta_and_links(self):
        doc = JsonApiDocument(
            data=JsonApiResource(type="articles", id="1"),
            meta={"total": 100},
            links={"self": "/articles/1"},
        )
        assert doc.meta == {"total": 100}
        assert doc.links == {"self": "/articles/1"}

    def test_document_with_included(self):
        doc = JsonApiDocument(
            data=JsonApiResource(type="articles", id="1"),
            included=[JsonApiResource(type="people", id="5", attributes={"name": "Author"})],
        )
        assert len(doc.included) == 1
        assert doc.included[0].type == "people"

    def test_document_with_jsonapi_version(self):
        doc = JsonApiDocument(
            data=JsonApiResource(type="articles", id="1"),
            jsonapi={"version": "1.1"},
        )
        assert doc.jsonapi == {"version": "1.1"}

    def test_to_dict_single_resource(self):
        doc = JsonApiDocument(
            data=JsonApiResource(
                type="articles",
                attributes={"title": "Hello"},
                relationships={
                    "author": JsonApiRelationship.to_one("people", "1"),
                },
            )
        )
        d = doc.to_dict()
        assert d["data"]["type"] == "articles"
        assert d["data"]["attributes"] == {"title": "Hello"}
        assert d["data"]["relationships"]["author"]["data"] == {
            "type": "people",
            "id": "1",
        }
        assert "id" not in d["data"]

    def test_to_dict_collection(self):
        doc = JsonApiDocument(
            data=[
                JsonApiResource(type="articles", id="1", attributes={"title": "A"}),
                JsonApiResource(type="articles", id="2", attributes={"title": "B"}),
            ]
        )
        d = doc.to_dict()
        assert isinstance(d["data"], list)
        assert len(d["data"]) == 2
        assert d["data"][0]["id"] == "1"

    def test_to_dict_error_document(self):
        doc = JsonApiDocument(
            errors=[
                JsonApiError(
                    status="422",
                    title="Invalid",
                    source={"pointer": "/data/attributes/title"},
                )
            ]
        )
        d = doc.to_dict()
        assert "data" not in d
        assert len(d["errors"]) == 1
        assert d["errors"][0]["status"] == "422"
        assert d["errors"][0]["source"] == {"pointer": "/data/attributes/title"}

    def test_to_dict_excludes_none_fields(self):
        doc = JsonApiDocument(
            data=JsonApiResource(type="articles", id="1")
        )
        d = doc.to_dict()
        assert "attributes" not in d["data"]
        assert "relationships" not in d["data"]
        assert "meta" not in d
        assert "links" not in d
        assert "included" not in d
        assert "jsonapi" not in d

    def test_to_dict_with_included(self):
        doc = JsonApiDocument(
            data=JsonApiResource(type="articles", id="1"),
            included=[
                JsonApiResource(type="people", id="5", attributes={"name": "Bob"}),
            ],
        )
        d = doc.to_dict()
        assert len(d["included"]) == 1
        assert d["included"][0]["type"] == "people"
        assert d["included"][0]["attributes"] == {"name": "Bob"}

    def test_to_dict_to_many_relationship(self):
        doc = JsonApiDocument(
            data=JsonApiResource(
                type="articles",
                id="1",
                relationships={
                    "tags": JsonApiRelationship.to_many([("tags", "1"), ("tags", "2")]),
                },
            )
        )
        d = doc.to_dict()
        tags = d["data"]["relationships"]["tags"]["data"]
        assert len(tags) == 2
        assert tags[0] == {"type": "tags", "id": "1"}
