from pytest_swag.adapters.jsonapi.schema import (
    jsonapi_base_schemas,
    resource_schema,
    response_document_schema,
    request_document_schema,
)


class TestJsonApiBaseSchemas:
    def test_returns_all_required_schema_names(self):
        schemas = jsonapi_base_schemas()
        expected_keys = {
            "JsonApiDocument",
            "JsonApiResource",
            "JsonApiRelationship",
            "JsonApiResourceLinkage",
            "JsonApiError",
            "JsonApiErrors",
            "JsonApiLinks",
            "JsonApiVersionObject",
        }
        assert set(schemas.keys()) == expected_keys

    def test_resource_has_required_type_and_id(self):
        schemas = jsonapi_base_schemas()
        resource = schemas["JsonApiResource"]
        assert resource["type"] == "object"
        assert "type" in resource["required"]
        assert "id" in resource["required"]

    def test_error_schema_has_standard_fields(self):
        schemas = jsonapi_base_schemas()
        error = schemas["JsonApiError"]
        props = error["properties"]
        assert "status" in props
        assert "title" in props
        assert "detail" in props
        assert "code" in props
        assert "source" in props

    def test_links_has_pagination_fields(self):
        schemas = jsonapi_base_schemas()
        links = schemas["JsonApiLinks"]
        props = links["properties"]
        for key in ("self", "related", "first", "last", "prev", "next"):
            assert key in props

    def test_errors_document_requires_errors_array(self):
        schemas = jsonapi_base_schemas()
        errors = schemas["JsonApiErrors"]
        assert "errors" in errors["required"]
        assert errors["properties"]["errors"]["type"] == "array"

    def test_linkage_requires_type_and_id(self):
        schemas = jsonapi_base_schemas()
        linkage = schemas["JsonApiResourceLinkage"]
        assert "type" in linkage["required"]
        assert "id" in linkage["required"]


class TestResourceSchema:
    def test_basic_resource_schema(self):
        schema = resource_schema(
            "articles",
            attributes_schema={
                "title": {"type": "string"},
                "body": {"type": "string"},
            },
        )
        assert schema["allOf"][0] == {"$ref": "#/components/schemas/JsonApiResource"}
        attrs = schema["allOf"][1]["properties"]["attributes"]["properties"]
        assert "title" in attrs
        assert "body" in attrs

    def test_resource_schema_with_relationships(self):
        schema = resource_schema(
            "articles",
            attributes_schema={"title": {"type": "string"}},
            relationships={"author": "people", "tags": "tags"},
        )
        rels = schema["allOf"][1]["properties"]["relationships"]["properties"]
        assert "author" in rels
        assert "tags" in rels

    def test_resource_schema_name_is_pascal_case(self):
        schema = resource_schema("blog-posts", attributes_schema={})
        assert "allOf" in schema


class TestResponseDocumentSchema:
    def test_single_resource_response(self):
        schema = response_document_schema("articles", is_collection=False)
        data = schema["properties"]["data"]
        assert data == {"$ref": "#/components/schemas/ArticlesResource"}

    def test_collection_response(self):
        schema = response_document_schema("articles", is_collection=True)
        data = schema["properties"]["data"]
        assert data["type"] == "array"
        assert data["items"] == {"$ref": "#/components/schemas/ArticlesResource"}

    def test_response_includes_meta_and_links(self):
        schema = response_document_schema("articles")
        props = schema["properties"]
        assert "meta" in props
        assert "links" in props


class TestRequestDocumentSchema:
    def test_request_document_no_id_required(self):
        schema = request_document_schema("articles")
        data = schema["properties"]["data"]
        assert data["$ref"] == "#/components/schemas/ArticlesResource"
        assert "data" in schema["required"]
