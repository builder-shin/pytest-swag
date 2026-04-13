from __future__ import annotations

from dataclasses import dataclass


@dataclass
class JsonApiResource:
    type: str
    id: str | None = None
    attributes: dict | None = None
    relationships: dict[str, JsonApiRelationship] | None = None
    links: dict | None = None
    meta: dict | None = None


@dataclass
class JsonApiRelationship:
    data: JsonApiResource | list[JsonApiResource] | None = None
    links: dict | None = None
    meta: dict | None = None

    @classmethod
    def to_one(cls, type: str, id: str) -> JsonApiRelationship:
        return cls(data=JsonApiResource(type=type, id=id))

    @classmethod
    def to_many(cls, items: list[tuple[str, str]]) -> JsonApiRelationship:
        return cls(data=[JsonApiResource(type=t, id=i) for t, i in items])


@dataclass
class JsonApiError:
    status: str | None = None
    title: str | None = None
    detail: str | None = None
    code: str | None = None
    source: dict | None = None
    meta: dict | None = None


@dataclass
class JsonApiDocument:
    data: JsonApiResource | list[JsonApiResource] | None = None
    errors: list[JsonApiError] | None = None
    meta: dict | None = None
    links: dict | None = None
    included: list[JsonApiResource] | None = None
    jsonapi: dict | None = None

    def to_dict(self) -> dict:
        result: dict = {}
        if self.data is not None:
            if isinstance(self.data, list):
                result["data"] = [_resource_to_dict(r) for r in self.data]
            else:
                result["data"] = _resource_to_dict(self.data)
        if self.errors is not None:
            result["errors"] = [_error_to_dict(e) for e in self.errors]
        if self.meta is not None:
            result["meta"] = self.meta
        if self.links is not None:
            result["links"] = self.links
        if self.included is not None:
            result["included"] = [_resource_to_dict(r) for r in self.included]
        if self.jsonapi is not None:
            result["jsonapi"] = self.jsonapi
        return result


def _resource_to_dict(r: JsonApiResource) -> dict:
    d: dict = {"type": r.type}
    if r.id is not None:
        d["id"] = r.id
    if r.attributes is not None:
        d["attributes"] = r.attributes
    if r.relationships is not None:
        d["relationships"] = {
            name: _relationship_to_dict(rel)
            for name, rel in r.relationships.items()
        }
    if r.links is not None:
        d["links"] = r.links
    if r.meta is not None:
        d["meta"] = r.meta
    return d


def _relationship_to_dict(rel: JsonApiRelationship) -> dict:
    d: dict = {}
    if rel.data is not None:
        if isinstance(rel.data, list):
            d["data"] = [{"type": r.type, "id": r.id} for r in rel.data]
        else:
            d["data"] = {"type": rel.data.type, "id": rel.data.id}
    if rel.links is not None:
        d["links"] = rel.links
    if rel.meta is not None:
        d["meta"] = rel.meta
    return d


def _error_to_dict(e: JsonApiError) -> dict:
    d: dict = {}
    if e.status is not None:
        d["status"] = e.status
    if e.title is not None:
        d["title"] = e.title
    if e.detail is not None:
        d["detail"] = e.detail
    if e.code is not None:
        d["code"] = e.code
    if e.source is not None:
        d["source"] = e.source
    if e.meta is not None:
        d["meta"] = e.meta
    return d
