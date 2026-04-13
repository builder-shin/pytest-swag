import json
from pathlib import Path

import pytest
from pytest_swag.config import SwagConfig
from pytest_swag.generator import SwagGenerator


class TestGenerateDoc:
    def test_generates_valid_openapi_structure(self):
        config = SwagConfig.from_dict({
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
        })
        paths = {
            "/blogs": {
                "get": {
                    "summary": "List blogs",
                    "responses": {
                        200: {"description": "OK"},
                    },
                },
            },
        }
        gen = SwagGenerator(config=config, paths=paths)
        doc = gen.generate()
        assert doc["openapi"] == "3.1.0"
        assert doc["info"]["title"] == "Test API"
        assert "/blogs" in doc["paths"]

    def test_responses_keys_are_strings(self):
        config = SwagConfig()
        paths = {
            "/blogs": {
                "get": {
                    "summary": "List",
                    "responses": {200: {"description": "OK"}},
                },
            },
        }
        gen = SwagGenerator(config=config, paths=paths)
        doc = gen.generate()
        responses = doc["paths"]["/blogs"]["get"]["responses"]
        assert "200" in responses
        assert 200 not in responses


class TestComponentSchemas:
    def test_includes_component_schemas(self):
        config = SwagConfig()
        schemas = {
            "Blog": {
                "type": "object",
                "properties": {"id": {"type": "integer"}},
            }
        }
        gen = SwagGenerator(config=config, paths={}, component_schemas=schemas)
        doc = gen.generate()
        assert doc["components"]["schemas"]["Blog"]["type"] == "object"

    def test_no_components_when_empty(self):
        config = SwagConfig()
        gen = SwagGenerator(config=config, paths={})
        doc = gen.generate()
        assert "components" not in doc


class TestSecuritySchemes:
    def test_includes_security_schemes(self):
        config = SwagConfig()
        security_schemes = {
            "BearerAuth": {"type": "http", "scheme": "bearer"},
        }
        gen = SwagGenerator(config=config, paths={}, security_schemes=security_schemes)
        doc = gen.generate()
        assert doc["components"]["securitySchemes"]["BearerAuth"]["type"] == "http"


class TestWriteFile:
    def test_write_json(self, tmp_path):
        config = SwagConfig.from_dict({"output_path": str(tmp_path / "api.json"), "output_format": "json"})
        paths = {"/blogs": {"get": {"summary": "List", "responses": {200: {"description": "OK"}}}}}
        gen = SwagGenerator(config=config, paths=paths)
        gen.write()
        output = tmp_path / "api.json"
        assert output.exists()
        data = json.loads(output.read_text())
        assert data["paths"]["/blogs"]["get"]["summary"] == "List"

    def test_write_yaml(self, tmp_path):
        pytest.importorskip("yaml")
        import yaml

        config = SwagConfig.from_dict({"output_path": str(tmp_path / "api.yaml"), "output_format": "yaml"})
        paths = {"/blogs": {"get": {"summary": "List", "responses": {200: {"description": "OK"}}}}}
        gen = SwagGenerator(config=config, paths=paths)
        gen.write()
        output = tmp_path / "api.yaml"
        assert output.exists()
        data = yaml.safe_load(output.read_text())
        assert data["paths"]["/blogs"]["get"]["summary"] == "List"

    def test_write_both(self, tmp_path):
        pytest.importorskip("yaml")
        config = SwagConfig.from_dict({
            "output_path": str(tmp_path / "api.json"),
            "output_format": "both",
        })
        paths = {"/blogs": {"get": {"summary": "List", "responses": {200: {"description": "OK"}}}}}
        gen = SwagGenerator(config=config, paths=paths)
        gen.write()
        assert (tmp_path / "api.json").exists()
        assert (tmp_path / "api.yaml").exists()

    def test_creates_parent_directories(self, tmp_path):
        config = SwagConfig.from_dict({
            "output_path": str(tmp_path / "docs" / "nested" / "api.json"),
        })
        gen = SwagGenerator(config=config, paths={})
        gen.write()
        assert (tmp_path / "docs" / "nested" / "api.json").exists()
