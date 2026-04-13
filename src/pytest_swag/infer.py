from __future__ import annotations


def infer_schema(value: object) -> dict:
    if value is None:
        return {"nullable": True}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    if isinstance(value, str):
        return {"type": "string"}
    if isinstance(value, list):
        if not value:
            return {"type": "array"}
        return {"type": "array", "items": infer_schema(value[0])}
    if isinstance(value, dict):
        properties = {k: infer_schema(v) for k, v in value.items()}
        return {"type": "object", "properties": properties}
    return {}
