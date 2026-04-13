from __future__ import annotations

from pytest_swag.builder import SwagBuilder
from pytest_swag.validator import SwagValidator


def _extract_body(response: object) -> object | None:
    content_type = getattr(response, "headers", {}).get("content-type", "")
    if "application/json" not in content_type and "application/vnd.api+json" not in content_type:
        return None
    try:
        return response.json()
    except Exception:
        return None


class HttpxSwagBuilder(SwagBuilder):
    def __init__(self) -> None:
        super().__init__()
        self._client: object | None = None
        self._base_url: str | None = None

    def run_test(
        self,
        *,
        client: object | None = None,
        base_url: str | None = None,
        json: object = None,
    ) -> object:
        from pytest_swag.builder import SwagBuildError

        resolved_client = client or self._client
        if resolved_client is None:
            raise SwagBuildError(
                "No HTTP client available. "
                "Provide swag_client fixture or configure servers in swag_config."
            )

        url = self._path
        params = {}
        headers = {}

        for param in self._parameters:
            if param["in"] == "path":
                if param.get("value") is None:
                    raise SwagBuildError(
                        f"Parameter '{param['name']}' requires a value for run_test()"
                    )
                url = url.replace("{" + param["name"] + "}", str(param["value"]))
            elif param["in"] == "query" and param.get("value") is not None:
                params[param["name"]] = param["value"]
            elif param["in"] == "header" and param.get("value") is not None:
                headers[param["name"]] = param["value"]

        resolved_base = base_url or self._base_url or ""
        full_url = resolved_base + url

        kwargs: dict = {}
        if params:
            kwargs["params"] = params
        if headers:
            kwargs["headers"] = headers
        if json is not None:
            kwargs["json"] = json

        method_fn = getattr(resolved_client, self._method)
        response = method_fn(full_url, **kwargs)

        if self._responses:
            self.validate_response(response)
        else:
            self.capture_response(response)

        return response

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
        if response.status_code in self._responses:
            self._responses[response.status_code]["example"] = body

    def capture_response(
        self,
        response: object,
        *,
        infer_schema: bool = True,
    ) -> None:
        body = _extract_body(response)
        self.capture(response.status_code, body, infer_schema=infer_schema)
