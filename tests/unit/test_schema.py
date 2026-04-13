from pytest_swag.schema import make_openapi_skeleton


class TestMakeOpenAPISkeleton:
    def test_skeleton_30(self):
        result = make_openapi_skeleton(
            openapi="3.0.3",
            info={"title": "Test", "version": "1.0.0"},
        )
        assert result["openapi"] == "3.0.3"
        assert result["info"] == {"title": "Test", "version": "1.0.0"}
        assert result["paths"] == {}
        assert "components" not in result

    def test_skeleton_31(self):
        result = make_openapi_skeleton(
            openapi="3.1.0",
            info={"title": "Test", "version": "1.0.0"},
        )
        assert result["openapi"] == "3.1.0"

    def test_skeleton_with_servers(self):
        result = make_openapi_skeleton(
            openapi="3.1.0",
            info={"title": "Test", "version": "1.0.0"},
            servers=[{"url": "https://api.example.com"}],
        )
        assert result["servers"] == [{"url": "https://api.example.com"}]

    def test_skeleton_with_security(self):
        result = make_openapi_skeleton(
            openapi="3.1.0",
            info={"title": "Test", "version": "1.0.0"},
            security=[{"BearerAuth": []}],
        )
        assert result["security"] == [{"BearerAuth": []}]

    def test_skeleton_without_optional_fields(self):
        result = make_openapi_skeleton(
            openapi="3.1.0",
            info={"title": "Test", "version": "1.0.0"},
        )
        assert "servers" not in result
        assert "security" not in result
