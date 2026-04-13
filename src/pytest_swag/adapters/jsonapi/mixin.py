from __future__ import annotations

from typing import Self

from pytest_swag.builder import SwagBuilder
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
