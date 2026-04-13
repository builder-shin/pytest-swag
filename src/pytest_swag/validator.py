from __future__ import annotations

import copy

import jsonschema


class SwagValidationError(AssertionError):
    pass


class SwagValidator:
    def __init__(
        self,
        *,
        responses: dict[int, dict],
        path: str,
        method: str,
        component_schemas: dict | None = None,
    ) -> None:
        self._responses = responses
        self._path = path
        self._method = method.upper()
        self._component_schemas = component_schemas or {}

    def validate(self, status_code: int, body: object) -> None:
        if status_code not in self._responses:
            raise SwagValidationError(
                f"Undocumented status code: {status_code} for {self._method} {self._path}"
            )
        schema = self._responses[status_code].get("schema")
        if schema is None or body is None:
            return
        resolved_schema = self._resolve_all_refs(schema)
        try:
            jsonschema.validate(instance=body, schema=resolved_schema)
        except jsonschema.ValidationError as e:
            raise SwagValidationError(
                f"Schema validation failed for {self._method} {self._path} → {status_code}\n\n"
                f"Path: $.{'.'.join(str(p) for p in e.absolute_path)}\n"
                f"Error: {e.message}"
            ) from None

    def _resolve_all_refs(self, schema: dict) -> dict:
        if not isinstance(schema, dict):
            return schema
        if "$ref" in schema:
            ref = schema["$ref"]
            prefix = "#/components/schemas/"
            if ref.startswith(prefix):
                name = ref[len(prefix) :]
                resolved = self._component_schemas.get(name)
                if resolved is None:
                    raise SwagValidationError(
                        f"Unresolved $ref: {ref} — schema '{name}' not found in component_schemas"
                    )
                return self._resolve_all_refs(copy.deepcopy(resolved))
            return schema
        result = {}
        for key, value in schema.items():
            if isinstance(value, dict):
                result[key] = self._resolve_all_refs(value)
            elif isinstance(value, list):
                result[key] = [
                    self._resolve_all_refs(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
