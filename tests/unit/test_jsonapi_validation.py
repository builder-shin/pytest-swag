from pytest_swag.adapters.jsonapi.validation import (
    JsonApiResponseValidator,
    JsonApiValidationError,
)


class TestValidateCompoundDocument:
    def test_valid_compound_document(self):
        body = {
            "data": {
                "type": "articles",
                "id": "1",
                "relationships": {
                    "author": {"data": {"type": "people", "id": "5"}},
                },
            },
            "included": [
                {"type": "people", "id": "5", "attributes": {"name": "Bob"}},
            ],
        }
        errors = JsonApiResponseValidator.validate_compound_document(body)
        assert errors == []

    def test_included_missing_type(self):
        body = {
            "data": {"type": "articles", "id": "1"},
            "included": [{"id": "5", "attributes": {"name": "Bob"}}],
        }
        errors = JsonApiResponseValidator.validate_compound_document(body)
        assert any("type" in e for e in errors)

    def test_included_missing_id(self):
        body = {
            "data": {"type": "articles", "id": "1"},
            "included": [{"type": "people", "attributes": {"name": "Bob"}}],
        }
        errors = JsonApiResponseValidator.validate_compound_document(body)
        assert any("id" in e for e in errors)

    def test_duplicate_in_included(self):
        body = {
            "data": {
                "type": "articles",
                "id": "1",
                "relationships": {
                    "author": {"data": {"type": "people", "id": "5"}},
                },
            },
            "included": [
                {"type": "people", "id": "5", "attributes": {"name": "Bob"}},
                {"type": "people", "id": "5", "attributes": {"name": "Bob2"}},
            ],
        }
        errors = JsonApiResponseValidator.validate_compound_document(body)
        assert any("duplicate" in e.lower() for e in errors)

    def test_orphan_in_included(self):
        body = {
            "data": {"type": "articles", "id": "1"},
            "included": [
                {"type": "people", "id": "5", "attributes": {"name": "Bob"}},
            ],
        }
        errors = JsonApiResponseValidator.validate_compound_document(body)
        assert any("orphan" in e.lower() for e in errors)

    def test_missing_from_included(self):
        body = {
            "data": {
                "type": "articles",
                "id": "1",
                "relationships": {
                    "author": {"data": {"type": "people", "id": "5"}},
                },
            },
            "included": [],
        }
        errors = JsonApiResponseValidator.validate_compound_document(body)
        assert any("missing" in e.lower() for e in errors)

    def test_no_included_key_passes(self):
        body = {"data": {"type": "articles", "id": "1"}}
        errors = JsonApiResponseValidator.validate_compound_document(body)
        assert errors == []

    def test_collection_with_included(self):
        body = {
            "data": [
                {
                    "type": "articles",
                    "id": "1",
                    "relationships": {
                        "author": {"data": {"type": "people", "id": "5"}},
                    },
                },
                {
                    "type": "articles",
                    "id": "2",
                    "relationships": {
                        "author": {"data": {"type": "people", "id": "5"}},
                    },
                },
            ],
            "included": [
                {"type": "people", "id": "5", "attributes": {"name": "Bob"}},
            ],
        }
        errors = JsonApiResponseValidator.validate_compound_document(body)
        assert errors == []

    def test_to_many_relationship(self):
        body = {
            "data": {
                "type": "articles",
                "id": "1",
                "relationships": {
                    "tags": {
                        "data": [
                            {"type": "tags", "id": "1"},
                            {"type": "tags", "id": "2"},
                        ]
                    },
                },
            },
            "included": [
                {"type": "tags", "id": "1", "attributes": {"name": "python"}},
                {"type": "tags", "id": "2", "attributes": {"name": "testing"}},
            ],
        }
        errors = JsonApiResponseValidator.validate_compound_document(body)
        assert errors == []


class TestValidateJsonapiMember:
    def test_no_jsonapi_member_passes(self):
        body = {"data": {"type": "articles", "id": "1"}}
        errors = JsonApiResponseValidator.validate_jsonapi_member(body)
        assert errors == []

    def test_valid_jsonapi_member(self):
        body = {
            "data": {"type": "articles", "id": "1"},
            "jsonapi": {"version": "1.1"},
        }
        errors = JsonApiResponseValidator.validate_jsonapi_member(body)
        assert errors == []

    def test_jsonapi_not_dict(self):
        body = {
            "data": {"type": "articles", "id": "1"},
            "jsonapi": "1.1",
        }
        errors = JsonApiResponseValidator.validate_jsonapi_member(body)
        assert len(errors) == 1

    def test_version_not_string(self):
        body = {
            "data": {"type": "articles", "id": "1"},
            "jsonapi": {"version": 1.1},
        }
        errors = JsonApiResponseValidator.validate_jsonapi_member(body)
        assert len(errors) == 1

    def test_jsonapi_without_version_passes(self):
        body = {
            "data": {"type": "articles", "id": "1"},
            "jsonapi": {"meta": {"info": "test"}},
        }
        errors = JsonApiResponseValidator.validate_jsonapi_member(body)
        assert errors == []


class TestJsonApiValidationError:
    def test_error_contains_all_messages(self):
        err = JsonApiValidationError(["error 1", "error 2"])
        assert err.errors == ["error 1", "error 2"]
        assert "error 1" in str(err)
        assert "error 2" in str(err)
