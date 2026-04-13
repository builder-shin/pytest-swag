from __future__ import annotations


def make_openapi_skeleton(
    *,
    openapi: str,
    info: dict,
    servers: list[dict] | None = None,
    security: list[dict] | None = None,
) -> dict:
    doc: dict = {
        "openapi": openapi,
        "info": info,
        "paths": {},
    }
    if servers:
        doc["servers"] = servers
    if security:
        doc["security"] = security
    return doc
