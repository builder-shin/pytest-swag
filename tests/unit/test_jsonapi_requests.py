import pytest
from unittest.mock import MagicMock

from pytest_swag.adapters.jsonapi.requests import JsonApiRequestsSwagBuilder
from pytest_swag.adapters.jsonapi.resource import JsonApiResource, JsonApiRelationship


class TestJsonApiRequestsSwagBuilder:
    def _make_response(
        self,
        status_code: int,
        json_data: object = None,
        content_type: str = "application/vnd.api+json",
    ) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        resp.headers = {"Content-Type": content_type}
        return resp

    def _make_client(self, method: str, response: MagicMock) -> MagicMock:
        client = MagicMock()
        getattr(client, method).return_value = response
        return client

    def test_run_test_sends_jsonapi_body(self):
        json_body = {
            "data": {
                "type": "articles",
                "attributes": {"title": "Hello"},
            }
        }
        resp = self._make_response(201, json_body)
        client = self._make_client("post", resp)

        b = JsonApiRequestsSwagBuilder()
        b.path("/articles").post()
        b.jsonapi_resource("articles", attributes={"title": "Hello"})

        b.run_test(client=client)

        call_kwargs = client.post.call_args[1]
        assert call_kwargs["json"]["data"]["type"] == "articles"
        assert call_kwargs["json"]["data"]["attributes"] == {"title": "Hello"}

    def test_run_test_sets_accept_header(self):
        resp = self._make_response(200, {"data": []})
        client = self._make_client("get", resp)

        b = JsonApiRequestsSwagBuilder()
        b.path("/articles").get()

        b.run_test(client=client)

        call_kwargs = client.get.call_args[1]
        assert call_kwargs["headers"]["Accept"] == "application/vnd.api+json"

    def test_run_test_with_pre_built_resource(self):
        resource = JsonApiResource(
            type="articles",
            attributes={"title": "Test"},
            relationships={"author": JsonApiRelationship.to_one("people", "1")},
        )
        resp_body = {
            "data": {
                "type": "articles",
                "id": "1",
                "attributes": {"title": "Test"},
            }
        }
        resp = self._make_response(201, resp_body)
        client = self._make_client("post", resp)

        b = JsonApiRequestsSwagBuilder()
        b.path("/articles").post()
        b.jsonapi_body(resource)

        b.run_test(client=client)

        call_kwargs = client.post.call_args[1]
        body = call_kwargs["json"]
        assert body["data"]["relationships"]["author"]["data"] == {
            "type": "people",
            "id": "1",
        }

    def test_run_test_validates_content_type(self):
        resp = self._make_response(200, {"data": []}, content_type="application/json")
        client = self._make_client("get", resp)

        b = JsonApiRequestsSwagBuilder()
        b.path("/articles").get()
        b.jsonapi_response(200, resource_type="articles", is_collection=True)

        with pytest.raises(AssertionError):
            b.run_test(client=client)

    def test_run_test_skips_content_type_check_when_overridden(self):
        resp = self._make_response(200, {"data": []}, content_type="application/json")
        client = self._make_client("get", resp)

        b = JsonApiRequestsSwagBuilder()
        b.path("/articles").get()
        b.jsonapi_content_type("application/json")
        b.jsonapi_response(200, resource_type="articles", is_collection=True)

        b.run_test(client=client)  # should not raise

    def test_run_test_without_jsonapi_body_sends_no_json(self):
        resp = self._make_response(200, {"data": [{"type": "articles", "id": "1"}]})
        client = self._make_client("get", resp)

        b = JsonApiRequestsSwagBuilder()
        b.path("/articles").get()

        b.run_test(client=client)

        call_kwargs = client.get.call_args[1]
        assert "json" not in call_kwargs

    def test_run_test_returns_response(self):
        resp = self._make_response(200, {"data": []})
        client = self._make_client("get", resp)

        b = JsonApiRequestsSwagBuilder()
        b.path("/articles").get()

        result = b.run_test(client=client)
        assert result is resp

    def test_chaining_full_flow(self):
        resp_body = {
            "data": {
                "type": "articles",
                "id": "1",
                "attributes": {"title": "Hello"},
            }
        }
        resp = self._make_response(201, resp_body)
        client = self._make_client("post", resp)

        b = JsonApiRequestsSwagBuilder()
        result = (
            b.path("/articles")
            .post()
            .jsonapi_resource("articles", attributes={"title": "Hello"})
            .jsonapi_relationship("author", type="people", id="1")
            .jsonapi_response(201, resource_type="articles")
            .run_test(client=client)
        )
        assert result is resp
        assert b._validated is True
