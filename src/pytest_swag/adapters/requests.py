from __future__ import annotations

from pytest_swag.builder import SwagBuilder
from pytest_swag.validator import SwagValidator


def _extract_body(response: object) -> object | None:
    content_type = getattr(response, "headers", {}).get("Content-Type", "")
    if "application/json" not in content_type:
        return None
    try:
        return response.json()
    except Exception:
        return None


def validate_response(
    response: object,
    *,
    responses: dict[int, dict],
    path: str,
    method: str,
    component_schemas: dict | None = None,
) -> None:
    validator = SwagValidator(
        responses=responses,
        path=path,
        method=method,
        component_schemas=component_schemas,
    )
    body = _extract_body(response)
    validator.validate(response.status_code, body)


class RequestsSwagBuilder(SwagBuilder):
    def validate_response(
        self,
        response: object,
        *,
        component_schemas: dict | None = None,
    ) -> None:
        body = _extract_body(response)
        validator = SwagValidator(
            responses=self._responses,
            path=self._path,
            method=self._method,
            component_schemas=component_schemas or {},
        )
        validator.validate(response.status_code, body)
        self._validated = True
