import pytest
from unittest.mock import MagicMock

from pytest_swag.adapters.httpx import HttpxSwagBuilder
from pytest_swag.builder import SwagBuildError
from pytest_swag.validator import SwagValidationError


class TestHttpxSwagBuilder:
    def _make_response(self, status_code=200, json_data=None, content_type="application/json"):
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        resp.headers = {"content-type": content_type}
        return resp

    def _make_client(self, method, response):
        client = MagicMock()
        getattr(client, method).return_value = response
        return client

    def test_run_test_builds_url_with_path_params(self):
        resp = self._make_response(200, {"id": 1})
        client = self._make_client("get", resp)

        b = HttpxSwagBuilder()
        b.path("/articles/{id}").get("Get article")
        b.parameter("id", in_="path", schema={"type": "string"}, value="42")

        b.run_test(client=client)
        call_url = client.get.call_args[0][0]
        assert call_url == "/articles/42"

    def test_run_test_appends_query_params(self):
        resp = self._make_response(200, [])
        client = self._make_client("get", resp)

        b = HttpxSwagBuilder()
        b.path("/articles").get("List")
        b.parameter("page", in_="query", schema={"type": "integer"}, value=1)

        b.run_test(client=client)
        call_kwargs = client.get.call_args[1]
        assert call_kwargs["params"] == {"page": 1}

    def test_run_test_sets_headers(self):
        resp = self._make_response(200, {})
        client = self._make_client("get", resp)

        b = HttpxSwagBuilder()
        b.path("/articles").get("List")
        b.parameter("X-Api-Key", in_="header", schema={"type": "string"}, value="secret")

        b.run_test(client=client)
        call_kwargs = client.get.call_args[1]
        assert call_kwargs["headers"] == {"X-Api-Key": "secret"}

    def test_run_test_sends_json(self):
        resp = self._make_response(201, {"id": 1})
        client = self._make_client("post", resp)

        b = HttpxSwagBuilder()
        b.path("/articles").post("Create")
        b.request_body(schema={"type": "object"})

        b.run_test(client=client, json={"title": "New"})
        call_kwargs = client.post.call_args[1]
        assert call_kwargs["json"] == {"title": "New"}

    def test_run_test_captures_when_no_schema(self):
        resp = self._make_response(200, {"id": 1})
        client = self._make_client("get", resp)

        b = HttpxSwagBuilder()
        b.path("/articles").get("List")

        result = b.run_test(client=client)
        assert result is resp
        assert b._captured is True

    def test_run_test_validates_when_schema_declared(self):
        resp = self._make_response(200, {"id": 1})
        client = self._make_client("get", resp)

        b = HttpxSwagBuilder()
        b.path("/articles").get("List")
        b.response(200, schema={"type": "object", "properties": {"id": {"type": "integer"}}})

        result = b.run_test(client=client)
        assert result is resp
        assert b._validated is True

    def test_run_test_with_base_url(self):
        resp = self._make_response(200, {})
        client = self._make_client("get", resp)

        b = HttpxSwagBuilder()
        b.path("/articles").get("List")

        b.run_test(client=client, base_url="http://localhost:8000")
        call_url = client.get.call_args[0][0]
        assert call_url == "http://localhost:8000/articles"

    def test_run_test_no_client_raises(self):
        b = HttpxSwagBuilder()
        b.path("/articles").get("List")

        with pytest.raises(SwagBuildError, match="No HTTP client available"):
            b.run_test()

    def test_run_test_returns_response(self):
        resp = self._make_response(200, {"id": 1})
        client = self._make_client("get", resp)

        b = HttpxSwagBuilder()
        b.path("/articles").get("List")

        result = b.run_test(client=client)
        assert result is resp

    def test_validate_response(self):
        b = HttpxSwagBuilder()
        b.path("/articles").get("List")
        b.response(200, schema={"type": "array", "items": {"type": "object"}})

        resp = self._make_response(200, [{"id": 1}])
        b.validate_response(resp)
        assert b._validated is True

    def test_capture_response(self):
        b = HttpxSwagBuilder()
        b.path("/articles").get("List")

        resp = self._make_response(200, [{"id": 1}])
        b.capture_response(resp)
        assert b._captured is True
        assert b._responses[200]["example"] == [{"id": 1}]
