from __future__ import annotations

from pytest_swag.adapters.requests import RequestsSwagBuilder
from pytest_swag.adapters.jsonapi.mixin import JsonApiMixin, JSONAPI_CONTENT_TYPE
from pytest_swag.adapters.jsonapi.resource import JsonApiDocument
from pytest_swag.adapters.jsonapi.schema import jsonapi_base_schemas, _to_pascal_case


def _auto_resource_schemas(resource_types: list[str]) -> dict:
    schemas = {}
    for rt in resource_types:
        if rt is None:
            continue
        name = f"{_to_pascal_case(rt)}Resource"
        schemas[name] = {"$ref": "#/components/schemas/JsonApiResource"}
    return schemas


class JsonApiRequestsSwagBuilder(JsonApiMixin, RequestsSwagBuilder):
    def __init__(self) -> None:
        super().__init__()
        self._init_jsonapi()

    def validate_response(
        self,
        response: object,
        *,
        component_schemas: dict | None = None,
    ) -> None:
        response_types = list(getattr(self, "_jsonapi_response_types", {}).values())
        schemas = {
            **jsonapi_base_schemas(),
            **_auto_resource_schemas(response_types),
            **(component_schemas or {}),
        }
        super().validate_response(response, component_schemas=schemas)

    def run_test(
        self,
        *,
        client: object | None = None,
        base_url: str | None = None,
        json: object = None,
    ) -> object:
        self._apply_jsonapi_headers()

        # Register query params into self._parameters so RequestsSwagBuilder picks them up
        if self._jsonapi_query is not None:
            query_params = self._jsonapi_query.to_query_params()
            for param_name, param_value in query_params.items():
                is_page = param_name.startswith("page[")
                schema_type = "integer" if is_page else "string"
                self.parameter(
                    param_name,
                    in_="query",
                    schema={"type": schema_type},
                    value=param_value,
                )
            self._jsonapi_query = None  # prevent double-registration in to_operation_dict

        if self._jsonapi_body is not None and json is None:
            doc = JsonApiDocument(
                data=self._jsonapi_body,
                meta=self._jsonapi_meta,
            )
            json = doc.to_dict()

        response = super().run_test(client=client, base_url=base_url, json=json)

        if not self._jsonapi_content_type_overridden:
            actual = getattr(response, "headers", {}).get("Content-Type", "")
            assert JSONAPI_CONTENT_TYPE in actual, (
                f"Expected Content-Type '{JSONAPI_CONTENT_TYPE}', got '{actual}'"
            )

        # Run JSON:API validations
        if self._jsonapi_validate_compound or self._jsonapi_validate_version:
            from pytest_swag.adapters.jsonapi.validation import (
                JsonApiResponseValidator,
                JsonApiValidationError,
            )

            body = response.json()
            errors: list[str] = []
            if self._jsonapi_validate_compound:
                errors.extend(JsonApiResponseValidator.validate_compound_document(body))
            if self._jsonapi_validate_version:
                errors.extend(JsonApiResponseValidator.validate_jsonapi_member(body))
            if errors:
                raise JsonApiValidationError(errors)

        return response
