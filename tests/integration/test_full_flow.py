import json


def test_complete_api_documentation(pytester, tmp_path):
    """Full flow: multiple endpoints, schemas, security, tags -> single OpenAPI doc."""
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "openapi": "3.1.0",
                "info": {{"title": "Blog API", "version": "1.0.0", "description": "A blog API"}},
                "servers": [{{"url": "https://api.example.com/v1"}}],
                "security": [{{"BearerAuth": []}}],
                "output_path": "{output}",
            }}

        @pytest.fixture(scope="session")
        def swag_schemas():
            return {{
                "Blog": {{
                    "type": "object",
                    "required": ["id", "title"],
                    "properties": {{
                        "id": {{"type": "integer"}},
                        "title": {{"type": "string"}},
                        "content": {{"type": "string"}},
                    }},
                }},
                "Error": {{
                    "type": "object",
                    "properties": {{
                        "message": {{"type": "string"}},
                    }},
                }},
            }}

        @pytest.fixture(scope="session")
        def swag_security_schemes():
            return {{
                "BearerAuth": {{
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }},
            }}
    """)
    pytester.makepyfile("""
        def test_list_blogs(swag):
            swag.path("/blogs").get("List all blogs")
            swag.tag("Blogs")
            swag.parameter("page", in_="query", schema={"type": "integer"})
            swag.response(200, description="OK", schema={
                "type": "array",
                "items": {"$ref": "#/components/schemas/Blog"},
            })
            swag.validate(200, [{"id": 1, "title": "Hello"}])

        def test_get_blog(swag):
            swag.path("/blogs/{id}").get("Get a blog")
            swag.tag("Blogs")
            swag.parameter("id", in_="path", schema={"type": "integer"})
            swag.response(200, schema={"$ref": "#/components/schemas/Blog"})
            swag.response(404, schema={"$ref": "#/components/schemas/Error"})
            swag.validate(200, {"id": 1, "title": "Hello"})

        def test_create_blog(swag):
            swag.path("/blogs").post("Create a blog")
            swag.tag("Blogs")
            swag.request_body(
                content_type="application/json",
                schema={
                    "type": "object",
                    "required": ["title"],
                    "properties": {"title": {"type": "string"}, "content": {"type": "string"}},
                },
            )
            swag.response(201, schema={"$ref": "#/components/schemas/Blog"})
            swag.validate(201, {"id": 2, "title": "New Blog"})

        def test_delete_blog(swag):
            swag.path("/blogs/{id}").delete("Delete a blog")
            swag.tag("Blogs")
            swag.parameter("id", in_="path", schema={"type": "integer"})
            swag.response(204, description="Deleted")
            swag.validate(204, None)
    """)
    result = pytester.runpytest("--swag", "-v")
    result.assert_outcomes(passed=4)

    assert output.exists()
    doc = json.loads(output.read_text())

    # Structure checks
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "Blog API"
    assert doc["servers"][0]["url"] == "https://api.example.com/v1"
    assert doc["security"] == [{"BearerAuth": []}]

    # Paths
    assert "/blogs" in doc["paths"]
    assert "get" in doc["paths"]["/blogs"]
    assert "post" in doc["paths"]["/blogs"]
    assert "/blogs/{id}" in doc["paths"]
    assert "get" in doc["paths"]["/blogs/{id}"]
    assert "delete" in doc["paths"]["/blogs/{id}"]

    # Components
    assert "Blog" in doc["components"]["schemas"]
    assert "Error" in doc["components"]["schemas"]
    assert "BearerAuth" in doc["components"]["securitySchemes"]

    # Tags
    assert doc["paths"]["/blogs"]["get"]["tags"] == ["Blogs"]


def test_multi_doc_output(pytester, tmp_path):
    """Multiple OpenAPI documents from a single test suite."""
    v1_output = tmp_path / "v1.json"
    v2_output = tmp_path / "v2.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return [
                {{"info": {{"title": "API v1", "version": "1.0.0"}}, "output_path": "{v1_output}"}},
                {{"info": {{"title": "API v2", "version": "2.0.0"}}, "output_path": "{v2_output}"}},
            ]
    """)
    pytester.makepyfile("""
        def test_v1_endpoint(swag):
            swag.doc("API v1")
            swag.path("/v1/blogs").get("List v1")
            swag.response(200, schema={"type": "array"})
            swag.validate(200, [])

        def test_v2_endpoint(swag):
            swag.doc("API v2")
            swag.path("/v2/blogs").get("List v2")
            swag.response(200, schema={"type": "array"})
            swag.validate(200, [])
    """)
    result = pytester.runpytest("--swag", "-v")
    result.assert_outcomes(passed=2)

    v1 = json.loads(v1_output.read_text())
    v2 = json.loads(v2_output.read_text())
    assert "/v1/blogs" in v1["paths"]
    assert "/v1/blogs" not in v2.get("paths", {})
    assert "/v2/blogs" in v2["paths"]
    assert "/v2/blogs" not in v1.get("paths", {})


def test_requests_adapter_flow(pytester, tmp_path):
    """requests adapter: validate_response() auto-extracts status_code and body."""
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "output_path": "{output}",
            }}
    """)
    pytester.makepyfile("""
        from unittest.mock import MagicMock

        def _mock_response(status_code, json_data):
            resp = MagicMock()
            resp.status_code = status_code
            resp.json.return_value = json_data
            resp.headers = {"Content-Type": "application/json"}
            return resp

        def test_with_requests_adapter(swag_requests):
            swag_requests.path("/blogs").get("List blogs")
            swag_requests.response(200, schema={
                "type": "array",
                "items": {"type": "object", "properties": {"id": {"type": "integer"}}},
            })
            resp = _mock_response(200, [{"id": 1}])
            swag_requests.validate_response(resp)
    """)
    result = pytester.runpytest("--swag", "-v")
    result.assert_outcomes(passed=1)
    assert output.exists()
    data = json.loads(output.read_text())
    assert "/blogs" in data["paths"]


def test_capture_flow(pytester, tmp_path):
    """capture() generates OpenAPI doc with inferred schema and example."""
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "output_path": "{output}",
            }}
    """)
    pytester.makepyfile("""
        def test_get_blog(swag):
            swag.path("/blogs/{id}").get("Get a blog")
            swag.parameter("id", in_="path", schema={"type": "string"})
            swag.capture(200, {"id": 1, "title": "Hello"})

        def test_delete_blog(swag):
            swag.path("/blogs/{id}").delete("Delete a blog")
            swag.parameter("id", in_="path", schema={"type": "string"})
            swag.capture(204, None)

        def test_capture_no_schema(swag):
            swag.path("/health").get("Health check")
            swag.capture(200, {"status": "ok"}, infer_schema=False)
    """)
    result = pytester.runpytest("--swag", "-v")
    result.assert_outcomes(passed=3)

    assert output.exists()
    doc = json.loads(output.read_text())

    # GET /blogs/{id} — inferred schema + example
    get_200 = doc["paths"]["/blogs/{id}"]["get"]["responses"]["200"]
    content = get_200["content"]["application/json"]
    assert content["schema"] == {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "title": {"type": "string"},
        },
    }
    assert content["example"] == {"id": 1, "title": "Hello"}

    # DELETE /blogs/{id} — no content for 204
    del_204 = doc["paths"]["/blogs/{id}"]["delete"]["responses"]["204"]
    assert "content" not in del_204

    # GET /health — example only, no schema
    health_200 = doc["paths"]["/health"]["get"]["responses"]["200"]
    health_content = health_200["content"]["application/json"]
    assert "schema" not in health_content
    assert health_content["example"] == {"status": "ok"}


def test_requests_capture_response_flow(pytester, tmp_path):
    """swag_requests.capture_response() auto-captures without schema."""
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "output_path": "{output}",
            }}
    """)
    pytester.makepyfile("""
        from unittest.mock import MagicMock

        def _mock_response(status_code, json_data):
            resp = MagicMock()
            resp.status_code = status_code
            resp.json.return_value = json_data
            resp.headers = {"Content-Type": "application/json"}
            return resp

        def test_capture_blog(swag_requests):
            swag_requests.path("/blogs").get("List blogs")
            resp = _mock_response(200, [{"id": 1, "title": "Hello"}])
            swag_requests.capture_response(resp)
    """)
    result = pytester.runpytest("--swag", "-v")
    result.assert_outcomes(passed=1)

    assert output.exists()
    doc = json.loads(output.read_text())
    content = doc["paths"]["/blogs"]["get"]["responses"]["200"]["content"]["application/json"]
    assert "schema" in content
    assert content["example"] == [{"id": 1, "title": "Hello"}]


def test_run_test_flow(pytester, tmp_path):
    """run_test() sends request via client and generates OpenAPI doc."""
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest
        from unittest.mock import MagicMock

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "output_path": "{output}",
            }}

        @pytest.fixture
        def swag_client():
            client = MagicMock()
            def make_response(url, **kwargs):
                resp = MagicMock()
                resp.status_code = 200
                resp.json.return_value = {{"id": 1, "title": "Hello"}}
                resp.headers = {{"Content-Type": "application/json"}}
                return resp
            client.get = make_response
            return client
    """)
    pytester.makepyfile("""
        def test_get_blog(swag_requests):
            swag_requests.path("/blogs/{id}").get("Get a blog")
            swag_requests.parameter("id", in_="path", schema={"type": "string"}, value="1")

            response = swag_requests.run_test()
            assert response.status_code == 200
            assert response.json() == {"id": 1, "title": "Hello"}
    """)
    result = pytester.runpytest("--swag", "-v")
    result.assert_outcomes(passed=1)

    assert output.exists()
    doc = json.loads(output.read_text())

    get_op = doc["paths"]["/blogs/{id}"]["get"]
    assert get_op["summary"] == "Get a blog"
    resp_200 = get_op["responses"]["200"]
    content = resp_200["content"]["application/json"]
    assert "schema" in content
    assert content["example"] == {"id": 1, "title": "Hello"}


def test_run_test_with_schema_validation(pytester, tmp_path):
    """run_test() validates against declared schema and captures."""
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest
        from unittest.mock import MagicMock

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "output_path": "{output}",
            }}

        @pytest.fixture
        def swag_client():
            client = MagicMock()
            def make_response(url, **kwargs):
                resp = MagicMock()
                resp.status_code = 200
                resp.json.return_value = {{"id": 1, "title": "Hello"}}
                resp.headers = {{"Content-Type": "application/json"}}
                return resp
            client.get = make_response
            return client
    """)
    pytester.makepyfile("""
        def test_get_blog(swag_requests):
            swag_requests.path("/blogs").get("List blogs")
            swag_requests.response(200, schema={
                "type": "object",
                "properties": {"id": {"type": "integer"}, "title": {"type": "string"}},
            })

            response = swag_requests.run_test()
            assert response.json()["id"] == 1
    """)
    result = pytester.runpytest("--swag", "-v")
    result.assert_outcomes(passed=1)

    doc = json.loads(output.read_text())
    resp_200 = doc["paths"]["/blogs"]["get"]["responses"]["200"]
    assert resp_200["content"]["application/json"].get("example") == {"id": 1, "title": "Hello"}


def test_run_test_with_base_url_fallback(pytester, tmp_path):
    """run_test() uses servers URL when no swag_client fixture."""
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "output_path": "{output}",
                "servers": [{{"url": "http://testserver"}}],
            }}
    """)
    pytester.makepyfile("""
        from unittest.mock import MagicMock, patch

        def test_get_blog(swag_requests):
            swag_requests.path("/blogs").get("List blogs")

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = [{"id": 1}]
            mock_resp.headers = {"Content-Type": "application/json"}

            with patch("requests.get", return_value=mock_resp) as mock_get:
                response = swag_requests.run_test()
                mock_get.assert_called_once()
                call_url = mock_get.call_args[0][0]
                assert call_url == "http://testserver/blogs"
    """)
    result = pytester.runpytest("--swag", "-v")
    result.assert_outcomes(passed=1)
