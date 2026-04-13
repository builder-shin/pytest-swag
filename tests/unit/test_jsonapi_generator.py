from pytest_swag.config import SwagConfig
from pytest_swag.generator import SwagGenerator


class TestJsonApiGeneratorIntegration:
    def _make_config(self) -> SwagConfig:
        return SwagConfig.from_dict({
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
        })

    def test_merges_jsonapi_base_schemas_when_marker_present(self):
        config = self._make_config()
        paths = {
            "/articles": {
                "get": {
                    "summary": "List articles",
                    "responses": {
                        200: {
                            "description": "OK",
                            "schema": {"type": "object"},
                        }
                    },
                    "x-jsonapi": True,
                }
            }
        }
        gen = SwagGenerator(config=config, paths=paths)
        doc = gen.generate()

        schemas = doc.get("components", {}).get("schemas", {})
        assert "JsonApiResource" in schemas
        assert "JsonApiError" in schemas
        assert "JsonApiLinks" in schemas
        assert "JsonApiDocument" in schemas

    def test_does_not_merge_without_marker(self):
        config = self._make_config()
        paths = {
            "/blogs": {
                "get": {
                    "summary": "List blogs",
                    "responses": {
                        200: {"description": "OK", "schema": {"type": "object"}}
                    },
                }
            }
        }
        gen = SwagGenerator(config=config, paths=paths)
        doc = gen.generate()

        schemas = doc.get("components", {}).get("schemas", {})
        assert "JsonApiResource" not in schemas

    def test_merges_with_existing_component_schemas(self):
        config = self._make_config()
        paths = {
            "/articles": {
                "get": {
                    "summary": "List",
                    "responses": {200: {"description": "OK"}},
                    "x-jsonapi": True,
                }
            }
        }
        existing_schemas = {"CustomModel": {"type": "object"}}
        gen = SwagGenerator(
            config=config, paths=paths, component_schemas=existing_schemas
        )
        doc = gen.generate()

        schemas = doc["components"]["schemas"]
        assert "CustomModel" in schemas
        assert "JsonApiResource" in schemas

    def test_x_jsonapi_stripped_from_output(self):
        config = self._make_config()
        paths = {
            "/articles": {
                "get": {
                    "summary": "List",
                    "responses": {200: {"description": "OK"}},
                    "x-jsonapi": True,
                }
            }
        }
        gen = SwagGenerator(config=config, paths=paths)
        doc = gen.generate()

        get_op = doc["paths"]["/articles"]["get"]
        assert "x-jsonapi" not in get_op
