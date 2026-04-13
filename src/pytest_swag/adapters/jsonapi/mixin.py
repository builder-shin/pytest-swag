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


class JsonApiSwagBuilder(JsonApiMixin, SwagBuilder):
    def __init__(self) -> None:
        super().__init__()
        self._init_jsonapi()
