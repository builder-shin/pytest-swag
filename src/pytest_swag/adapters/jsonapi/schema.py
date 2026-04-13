from __future__ import annotations


def jsonapi_base_schemas() -> dict:
    return {
        "JsonApiDocument": {
            "type": "object",
            "properties": {
                "data": {},
                "errors": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/JsonApiError"},
                },
                "meta": {"type": "object"},
                "links": {"$ref": "#/components/schemas/JsonApiLinks"},
                "included": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/JsonApiResource"},
                },
                "jsonapi": {"$ref": "#/components/schemas/JsonApiVersionObject"},
            },
        },
        "JsonApiResource": {
            "type": "object",
            "required": ["type", "id"],
            "properties": {
                "type": {"type": "string"},
                "id": {"type": "string"},
                "attributes": {"type": "object"},
                "relationships": {"type": "object"},
                "links": {"$ref": "#/components/schemas/JsonApiLinks"},
                "meta": {"type": "object"},
            },
        },
        "JsonApiRelationship": {
            "type": "object",
            "properties": {
                "data": {},
                "links": {"$ref": "#/components/schemas/JsonApiLinks"},
                "meta": {"type": "object"},
            },
        },
        "JsonApiResourceLinkage": {
            "type": "object",
            "required": ["type", "id"],
            "properties": {
                "type": {"type": "string"},
                "id": {"type": "string"},
            },
        },
        "JsonApiError": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "title": {"type": "string"},
                "detail": {"type": "string"},
                "code": {"type": "string"},
                "source": {
                    "type": "object",
                    "properties": {
                        "pointer": {"type": "string"},
                        "parameter": {"type": "string"},
                    },
                },
                "meta": {"type": "object"},
            },
        },
        "JsonApiErrors": {
            "type": "object",
            "required": ["errors"],
            "properties": {
                "errors": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/JsonApiError"},
                },
            },
        },
        "JsonApiLinks": {
            "type": "object",
            "properties": {
                "self": {"type": "string", "format": "uri"},
                "related": {"type": "string", "format": "uri"},
                "first": {"type": "string", "format": "uri"},
                "last": {"type": "string", "format": "uri"},
                "prev": {"type": "string", "format": "uri", "nullable": True},
                "next": {"type": "string", "format": "uri", "nullable": True},
            },
        },
        "JsonApiVersionObject": {
            "type": "object",
            "properties": {
                "version": {"type": "string"},
            },
        },
    }


def _to_pascal_case(type_name: str) -> str:
    return "".join(part.capitalize() for part in type_name.replace("_", "-").split("-"))


def resource_schema(
    type_name: str,
    attributes_schema: dict,
    relationships: dict[str, str] | None = None,
) -> dict:
    extra_props: dict = {}
    if attributes_schema:
        extra_props["attributes"] = {
            "type": "object",
            "properties": attributes_schema,
        }
    if relationships:
        rel_props = {}
        for rel_name, rel_type in relationships.items():
            rel_props[rel_name] = {"$ref": "#/components/schemas/JsonApiRelationship"}
        extra_props["relationships"] = {
            "type": "object",
            "properties": rel_props,
        }
    return {
        "allOf": [
            {"$ref": "#/components/schemas/JsonApiResource"},
            {"properties": extra_props} if extra_props else {},
        ],
    }


def _resource_ref(type_name: str) -> str:
    return f"#/components/schemas/{_to_pascal_case(type_name)}Resource"


def response_document_schema(
    resource_type: str,
    is_collection: bool = False,
) -> dict:
    ref = _resource_ref(resource_type)
    if is_collection:
        data_schema = {"type": "array", "items": {"$ref": ref}}
    else:
        data_schema = {"$ref": ref}
    return {
        "type": "object",
        "properties": {
            "data": data_schema,
            "meta": {"type": "object"},
            "links": {"$ref": "#/components/schemas/JsonApiLinks"},
            "jsonapi": {"$ref": "#/components/schemas/JsonApiVersionObject"},
        },
    }


def request_document_schema(resource_type: str) -> dict:
    ref = _resource_ref(resource_type)
    return {
        "type": "object",
        "required": ["data"],
        "properties": {
            "data": {"$ref": ref},
            "meta": {"type": "object"},
        },
    }
