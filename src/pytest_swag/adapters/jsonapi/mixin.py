from __future__ import annotations

from typing import Self

from pytest_swag.builder import SwagBuilder
from pytest_swag.adapters.jsonapi.query import JsonApiQuery
from pytest_swag.adapters.jsonapi.resource import (
    JsonApiResource,
    JsonApiRelationship,
)

JSONAPI_CONTENT_TYPE = "application/vnd.api+json"


class JsonApiMixin:
    _jsonapi_body: JsonApiResource | None
    _jsonapi_meta: dict | None
    _jsonapi_content_type_overridden: bool

    def _init_jsonapi(self) -> None:
        self._jsonapi_body = None
        self._jsonapi_meta = None
        self._jsonapi_content_type_overridden = False
        self._jsonapi_query: JsonApiQuery | None = None
        self._jsonapi_validate_compound: bool = False
        self._jsonapi_validate_version: bool = False

    def jsonapi_resource(
        self,
        type: str,
        *,
        id: str | None = None,
        attributes: dict | None = None,
        relationships: dict | None = None,
    ) -> Self:
        self._jsonapi_body = JsonApiResource(
            type=type,
            id=id,
            attributes=attributes,
            relationships=relationships,
        )
        return self

    def jsonapi_relationship(self, name: str, *, type: str, id: str) -> Self:
        if self._jsonapi_body.relationships is None:
            self._jsonapi_body.relationships = {}
        self._jsonapi_body.relationships[name] = JsonApiRelationship.to_one(type, id)
        return self

    def jsonapi_relationships(
        self, name: str, *, items: list[tuple[str, str]]
    ) -> Self:
        if self._jsonapi_body.relationships is None:
            self._jsonapi_body.relationships = {}
        self._jsonapi_body.relationships[name] = JsonApiRelationship.to_many(items)
        return self

    def jsonapi_body(self, resource: JsonApiResource) -> Self:
        self._jsonapi_body = resource
        return self

    def jsonapi_meta(self, meta: dict) -> Self:
        self._jsonapi_meta = meta
        return self

    def jsonapi_fields(self, type: str, fields: list[str]) -> Self:
        if self._jsonapi_query is None:
            self._jsonapi_query = JsonApiQuery()
        if self._jsonapi_query.fields is None:
            self._jsonapi_query.fields = {}
        self._jsonapi_query.fields[type] = fields
        return self

    def jsonapi_include(self, *paths: str) -> Self:
        if self._jsonapi_query is None:
            self._jsonapi_query = JsonApiQuery()
        if self._jsonapi_query.include is None:
            self._jsonapi_query.include = []
        self._jsonapi_query.include.extend(paths)
        return self

    def jsonapi_filter(self, field: str, value: str | dict[str, str]) -> Self:
        if self._jsonapi_query is None:
            self._jsonapi_query = JsonApiQuery()
        if self._jsonapi_query.filter is None:
            self._jsonapi_query.filter = {}
        self._jsonapi_query.filter[field] = value
        return self

    def jsonapi_sort(self, *fields: str) -> Self:
        if self._jsonapi_query is None:
            self._jsonapi_query = JsonApiQuery()
        self._jsonapi_query.sort = list(fields)
        return self

    def jsonapi_page(self, *, number: int, size: int) -> Self:
        if self._jsonapi_query is None:
            self._jsonapi_query = JsonApiQuery()
        self._jsonapi_query.page = {"number": number, "size": size}
        return self

    def jsonapi_query(self, query: JsonApiQuery) -> Self:
        self._jsonapi_query = query
        return self

    def jsonapi_validate_compound(self, *, enabled: bool = True) -> Self:
        self._jsonapi_validate_compound = enabled
        return self

    def jsonapi_validate_version(self, *, enabled: bool = True) -> Self:
        self._jsonapi_validate_version = enabled
        return self

    def jsonapi_response(
        self,
        status_code: int,
        *,
        resource_type: str | None = None,
        is_collection: bool = False,
        description: str | None = None,
        schema: dict | None = None,
    ) -> Self:
        from pytest_swag.adapters.jsonapi.schema import response_document_schema

        if schema is None and resource_type is not None:
            schema = response_document_schema(resource_type, is_collection=is_collection)
        self._jsonapi_response_types = getattr(self, "_jsonapi_response_types", {})
        self._jsonapi_response_types[status_code] = resource_type
        self.response(status_code, description=description, schema=schema)
        return self

    def jsonapi_error_response(
        self,
        status_code: int,
        *,
        description: str | None = None,
    ) -> Self:
        schema = {
            "type": "object",
            "required": ["errors"],
            "properties": {
                "errors": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/JsonApiError"},
                },
            },
        }
        self.response(status_code, description=description, schema=schema)
        self._jsonapi_response_types = getattr(self, "_jsonapi_response_types", {})
        self._jsonapi_response_types[status_code] = None
        return self

    def _apply_jsonapi_headers(self) -> None:
        if not self._jsonapi_content_type_overridden:
            self.parameter(
                "Accept",
                in_="header",
                schema={"type": "string"},
                value=JSONAPI_CONTENT_TYPE,
            )

    def jsonapi_content_type(self, value: str) -> Self:
        self._jsonapi_content_type_overridden = True
        return self

    def to_operation_dict(self) -> dict:
        if self._jsonapi_body is not None:
            from pytest_swag.adapters.jsonapi.schema import request_document_schema

            schema = request_document_schema(self._jsonapi_body.type)
            self.request_body(content_type=JSONAPI_CONTENT_TYPE, schema=schema)

        # Add query parameters from _jsonapi_query
        if self._jsonapi_query is not None:
            query_params = self._jsonapi_query.to_query_params()
            for param_name, param_value in query_params.items():
                is_page = param_name.startswith("page[")
                schema_type = "integer" if is_page else "string"
                self.parameter(
                    param_name,
                    in_="query",
                    schema={"type": schema_type},
                    value=param_value,
                )

        op = super().to_operation_dict()

        has_jsonapi = (
            self._jsonapi_body is not None
            or getattr(self, "_jsonapi_response_types", None)
        )
        if has_jsonapi:
            op["x-jsonapi"] = True

        jsonapi_responses = getattr(self, "_jsonapi_response_types", {})
        if jsonapi_responses and "responses" in op:
            for code in jsonapi_responses:
                if code in op["responses"]:
                    resp = op["responses"][code]
                    if "content" in resp and "application/json" in resp["content"]:
                        resp["content"][JSONAPI_CONTENT_TYPE] = resp["content"].pop(
                            "application/json"
                        )

        return op


class JsonApiSwagBuilder(JsonApiMixin, SwagBuilder):
    def __init__(self) -> None:
        super().__init__()
        self._init_jsonapi()
