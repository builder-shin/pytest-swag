from __future__ import annotations

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
        resolved_schema = self._resolve_schema(schema)
        try:
            jsonschema.validate(instance=body, schema=resolved_schema)
        except jsonschema.ValidationError as e:
            raise SwagValidationError(
                f"Schema validation failed for {self._method} {self._path} → {status_code}\n\n"
                f"Path: $.{'.'.join(str(p) for p in e.absolute_path)}\n"
                f"Error: {e.message}"
            ) from None

    def _resolve_schema(self, schema: dict) -> dict:
        if "$ref" not in schema:
            return schema
        ref = schema["$ref"]
        prefix = "#/components/schemas/"
        if not ref.startswith(prefix):
            return schema
        name = ref[len(prefix):]
        resolved = self._component_schemas.get(name)
        if resolved is None:
            raise SwagValidationError(
                f"Unresolved $ref: {ref} — schema '{name}' not found in component_schemas"
            )
        return resolved
