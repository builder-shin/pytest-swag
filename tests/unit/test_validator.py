import pytest
from pytest_swag.validator import SwagValidator, SwagValidationError


class TestValidateStatusCode:
    def test_valid_status_code(self):
        v = SwagValidator(
            responses={200: {"description": "OK", "schema": None}},
            path="/blogs",
            method="get",
        )
        v.validate(200, {})  # should not raise

    def test_undocumented_status_code(self):
        v = SwagValidator(
            responses={200: {"description": "OK", "schema": None}},
            path="/blogs",
            method="get",
        )
        with pytest.raises(SwagValidationError, match="Undocumented status code: 404"):
            v.validate(404, {})


class TestValidateSchema:
    def test_valid_body(self):
        schema = {
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "integer"}},
        }
        v = SwagValidator(
            responses={200: {"description": "OK", "schema": schema}},
            path="/blogs",
            method="get",
        )
        v.validate(200, {"id": 1})  # should not raise

    def test_invalid_body_wrong_type(self):
        schema = {
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "integer"}},
        }
        v = SwagValidator(
            responses={200: {"description": "OK", "schema": schema}},
            path="/blogs",
            method="get",
        )
        with pytest.raises(SwagValidationError, match="Schema validation failed"):
            v.validate(200, {"id": "not_an_int"})

    def test_missing_required_field(self):
        schema = {
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "integer"}},
        }
        v = SwagValidator(
            responses={200: {"description": "OK", "schema": schema}},
            path="/blogs",
            method="get",
        )
        with pytest.raises(SwagValidationError, match="Schema validation failed"):
            v.validate(200, {})

    def test_no_schema_skips_validation(self):
        v = SwagValidator(
            responses={204: {"description": "No content", "schema": None}},
            path="/blogs/{id}",
            method="delete",
        )
        v.validate(204, None)  # should not raise


class TestValidateWithRef:
    def test_ref_resolved_against_component_schemas(self):
        schema = {"$ref": "#/components/schemas/Blog"}
        component_schemas = {
            "Blog": {
                "type": "object",
                "required": ["id"],
                "properties": {"id": {"type": "integer"}},
            }
        }
        v = SwagValidator(
            responses={200: {"description": "OK", "schema": schema}},
            path="/blogs/{id}",
            method="get",
            component_schemas=component_schemas,
        )
        v.validate(200, {"id": 1})  # should not raise

    def test_ref_validation_failure(self):
        schema = {"$ref": "#/components/schemas/Blog"}
        component_schemas = {
            "Blog": {
                "type": "object",
                "required": ["id"],
                "properties": {"id": {"type": "integer"}},
            }
        }
        v = SwagValidator(
            responses={200: {"description": "OK", "schema": schema}},
            path="/blogs/{id}",
            method="get",
            component_schemas=component_schemas,
        )
        with pytest.raises(SwagValidationError, match="Schema validation failed"):
            v.validate(200, {"id": "not_int"})


class TestErrorMessage:
    def test_error_includes_path_and_method(self):
        schema = {"type": "object", "properties": {"id": {"type": "integer"}}}
        v = SwagValidator(
            responses={200: {"description": "OK", "schema": schema}},
            path="/blogs",
            method="post",
        )
        with pytest.raises(SwagValidationError, match="POST /blogs"):
            v.validate(200, {"id": "wrong"})
