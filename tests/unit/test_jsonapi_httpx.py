import pytest
from unittest.mock import MagicMock

from pytest_swag.adapters.jsonapi.httpx import JsonApiHttpxSwagBuilder
from pytest_swag.adapters.jsonapi.resource import JsonApiResource, JsonApiRelationship
from pytest_swag.adapters.jsonapi.query import JsonApiQuery
from pytest_swag.adapters.jsonapi.validation import JsonApiValidationError


class TestJsonApiHttpxSwagBuilder:
    def _make_response(self, status_code=200, json_data=None, content_type="application/vnd.api+json"):
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        resp.headers = {"content-type": content_type}
        return resp

    def _make_client(self, method, response):
        client = MagicMock()
        getattr(client, method).return_value = response
        return client

    def test_run_test_sends_jsonapi_body(self):
        body = {"data": {"type": "articles", "attributes": {"title": "Hello"}}}
        resp = self._make_response(201, body)
        client = self._make_client("post", resp)

        b = JsonApiHttpxSwagBuilder()
        b.path("/articles").post()
        b.jsonapi_resource("articles", attributes={"title": "Hello"})

        b.run_test(client=client)

        call_kwargs = client.post.call_args[1]
        assert call_kwargs["json"]["data"]["type"] == "articles"

    def test_run_test_sets_accept_header(self):
        resp = self._make_response(200, {"data": []})
        client = self._make_client("get", resp)

        b = JsonApiHttpxSwagBuilder()
        b.path("/articles").get()

        b.run_test(client=client)

        call_kwargs = client.get.call_args[1]
        assert call_kwargs["headers"]["Accept"] == "application/vnd.api+json"

    def test_run_test_validates_content_type(self):
        resp = self._make_response(200, {"data": []}, content_type="application/json")
        client = self._make_client("get", resp)

        b = JsonApiHttpxSwagBuilder()
        b.path("/articles").get()
        b.jsonapi_response(200, resource_type="articles", is_collection=True)

        with pytest.raises(AssertionError):
            b.run_test(client=client)

    def test_query_params_sent(self):
        resp = self._make_response(200, {"data": []})
        client = self._make_client("get", resp)

        b = JsonApiHttpxSwagBuilder()
        b.path("/articles").get()
        b.jsonapi_include("author")
        b.jsonapi_filter("status", "published")

        b.run_test(client=client)

        call_kwargs = client.get.call_args[1]
        assert call_kwargs["params"]["include"] == "author"
        assert call_kwargs["params"]["filter[status]"] == "published"

    def test_compound_validation_passes(self):
        body = {
            "data": {
                "type": "articles", "id": "1",
                "relationships": {"author": {"data": {"type": "people", "id": "5"}}},
            },
            "included": [{"type": "people", "id": "5", "attributes": {"name": "Bob"}}],
        }
        resp = self._make_response(200, body)
        client = self._make_client("get", resp)

        b = JsonApiHttpxSwagBuilder()
        b.path("/articles/1").get()
        b.jsonapi_validate_compound()
        b.run_test(client=client)  # should not raise

    def test_compound_validation_fails_on_orphan(self):
        body = {
            "data": {"type": "articles", "id": "1"},
            "included": [{"type": "people", "id": "5"}],
        }
        resp = self._make_response(200, body)
        client = self._make_client("get", resp)

        b = JsonApiHttpxSwagBuilder()
        b.path("/articles/1").get()
        b.jsonapi_validate_compound()

        with pytest.raises(JsonApiValidationError, match="orphan"):
            b.run_test(client=client)

    def test_chaining_full_flow(self):
        body = {"data": {"type": "articles", "id": "1", "attributes": {"title": "Hi"}}}
        resp = self._make_response(201, body)
        client = self._make_client("post", resp)

        b = JsonApiHttpxSwagBuilder()
        result = (
            b.path("/articles")
            .post()
            .jsonapi_resource("articles", attributes={"title": "Hi"})
            .jsonapi_response(201, resource_type="articles")
            .run_test(client=client)
        )
        assert result is resp
        assert b._validated is True

    def test_run_test_returns_response(self):
        resp = self._make_response(200, {"data": []})
        client = self._make_client("get", resp)

        b = JsonApiHttpxSwagBuilder()
        b.path("/articles").get()

        result = b.run_test(client=client)
        assert result is resp
