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


class TestAutoCapture:
    def _make_response(self, status_code, json_data=None, content_type="application/json"):
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        resp.headers = {"Content-Type": content_type}
        return resp

    def test_validate_response_captures_body(self):
        builder = RequestsSwagBuilder()
        builder.path("/blogs").get("List blogs")
        builder.response(200, schema={"type": "array", "items": {"type": "object"}})

        resp = self._make_response(200, [{"id": 1}])
        builder.validate_response(resp)

        assert builder._responses[200].get("example") == [{"id": 1}]

    def test_validate_response_captures_none_for_no_json(self):
        builder = RequestsSwagBuilder()
        builder.path("/blogs/{id}").delete("Delete blog")
        builder.response(204, description="Deleted")

        resp = self._make_response(204, content_type="text/plain")

        builder.validate_response(resp)

        assert builder._responses[204].get("example") is None


class TestCaptureResponse:
    def _make_response(self, status_code, json_data=None, content_type="application/json"):
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        resp.headers = {"Content-Type": content_type}
        return resp

    def test_capture_response_infers_schema(self):
        builder = RequestsSwagBuilder()
        builder.path("/blogs").get("List blogs")
        resp = self._make_response(200, [{"id": 1, "title": "Hello"}])
        builder.capture_response(resp)

        assert builder._validated is True
        assert builder._responses[200]["example"] == [{"id": 1, "title": "Hello"}]
        assert builder._responses[200]["schema"] == {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                },
            },
        }

    def test_capture_response_without_inference(self):
        builder = RequestsSwagBuilder()
        builder.path("/blogs").get("List blogs")
        resp = self._make_response(200, {"id": 1})
        builder.capture_response(resp, infer_schema=False)

        assert builder._responses[200]["schema"] is None
        assert builder._responses[200]["example"] == {"id": 1}

    def test_capture_response_no_json_body(self):
        builder = RequestsSwagBuilder()
        builder.path("/blogs/{id}").delete("Delete blog")
        resp = self._make_response(204, content_type="text/plain")
        builder.capture_response(resp)

        assert builder._responses[204]["example"] is None
        assert builder._responses[204]["schema"] is None
