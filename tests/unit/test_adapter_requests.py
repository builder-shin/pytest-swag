import pytest
from unittest.mock import MagicMock
from pytest_swag.adapters.requests import validate_response, RequestsSwagBuilder
from pytest_swag.validator import SwagValidationError


class TestValidateResponse:
    def _make_response(self, status_code: int, json_data: object = None) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        resp.headers = {"Content-Type": "application/json"}
        return resp

    def test_valid_response(self):
        responses = {
            200: {
                "description": "OK",
                "schema": {"type": "object", "properties": {"id": {"type": "integer"}}},
            }
        }
        resp = self._make_response(200, {"id": 1})
        validate_response(resp, responses=responses, path="/blogs", method="get")

    def test_invalid_response_raises(self):
        responses = {
            200: {
                "description": "OK",
                "schema": {
                    "type": "object",
                    "required": ["id"],
                    "properties": {"id": {"type": "integer"}},
                },
            }
        }
        resp = self._make_response(200, {"id": "wrong"})
        with pytest.raises(SwagValidationError):
            validate_response(resp, responses=responses, path="/blogs", method="get")

    def test_no_content_type_skips_json_parse(self):
        responses = {204: {"description": "No content", "schema": None}}
        resp = self._make_response(204, None)
        resp.headers = {}
        validate_response(resp, responses=responses, path="/blogs/{id}", method="delete")


class TestRequestsSwagBuilder:
    def _make_response(self, status_code: int, json_data: object = None) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        resp.headers = {"Content-Type": "application/json"}
        return resp

    def test_validate_response_method(self):
        b = RequestsSwagBuilder()
        b.path("/blogs").get("List blogs")
        b.response(200, schema={"type": "array", "items": {"type": "object"}})
        resp = self._make_response(200, [{"id": 1}])
        b.validate_response(resp)
        assert b._validated is True

    def test_validate_response_fails_on_wrong_schema(self):
        b = RequestsSwagBuilder()
        b.path("/blogs").get("List blogs")
        b.response(
            200,
            schema={
                "type": "object",
                "required": ["id"],
                "properties": {"id": {"type": "integer"}},
            },
        )
        resp = self._make_response(200, {"id": "not_int"})
        with pytest.raises(SwagValidationError):
            b.validate_response(resp)

    def test_validate_response_extracts_body_from_json(self):
        b = RequestsSwagBuilder()
        b.path("/blogs").get("List")
        b.response(200, schema={"type": "object", "properties": {"name": {"type": "string"}}})
        resp = self._make_response(200, {"name": "hello"})
        b.validate_response(resp)  # should not raise

    def test_validate_response_no_body_for_204(self):
        b = RequestsSwagBuilder()
        b.path("/blogs/{id}").delete("Delete")
        b.response(204, description="Deleted")
        resp = self._make_response(204, None)
        resp.headers = {}
        b.validate_response(resp)
        assert b._validated is True
