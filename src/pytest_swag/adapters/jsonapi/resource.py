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
