from pytest_swag.config import SwagConfig


class TestSwagConfigDefaults:
    def test_default_openapi_version(self):
        config = SwagConfig()
        assert config.openapi == "3.1.0"

    def test_default_info(self):
        config = SwagConfig()
        assert config.info == {"title": "API", "version": "0.1.0"}

    def test_default_output_path(self):
        config = SwagConfig()
        assert config.output_path == "openapi.json"

    def test_default_output_format(self):
        config = SwagConfig()
        assert config.output_format == "json"


class TestSwagConfigFromDict:
    def test_from_dict_overrides_defaults(self):
        config = SwagConfig.from_dict(
            {
                "openapi": "3.0.3",
                "info": {"title": "Blog API", "version": "1.0.0"},
                "output_path": "docs/api.json",
                "output_format": "both",
            }
        )
        assert config.openapi == "3.0.3"
        assert config.info == {"title": "Blog API", "version": "1.0.0"}
        assert config.output_path == "docs/api.json"
        assert config.output_format == "both"

    def test_from_dict_partial_override(self):
        config = SwagConfig.from_dict({"openapi": "3.0.3"})
        assert config.openapi == "3.0.3"
        assert config.info == {"title": "API", "version": "0.1.0"}

    def test_from_dict_with_servers(self):
        config = SwagConfig.from_dict(
            {
                "servers": [{"url": "https://api.example.com"}],
            }
        )
        assert config.servers == [{"url": "https://api.example.com"}]

    def test_from_dict_with_security(self):
        config = SwagConfig.from_dict(
            {
                "security": [{"BearerAuth": []}],
            }
        )
        assert config.security == [{"BearerAuth": []}]


class TestSwagConfigFromPyproject:
    def test_reads_tool_pytest_swag_section(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            "[tool.pytest-swag]\n"
            'openapi = "3.0.3"\n'
            'output_path = "docs/api.yaml"\n'
            'output_format = "yaml"\n'
            "\n"
            "[tool.pytest-swag.info]\n"
            'title = "My API"\n'
            'version = "2.0.0"\n'
        )
        config = SwagConfig.from_pyproject(tmp_path)
        assert config.openapi == "3.0.3"
        assert config.info == {"title": "My API", "version": "2.0.0"}
        assert config.output_path == "docs/api.yaml"
        assert config.output_format == "yaml"

    def test_returns_defaults_when_no_pyproject(self, tmp_path):
        config = SwagConfig.from_pyproject(tmp_path)
        assert config.openapi == "3.1.0"

    def test_returns_defaults_when_no_section(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.ruff]\nline-length = 100\n")
        config = SwagConfig.from_pyproject(tmp_path)
        assert config.openapi == "3.1.0"


class TestSwagConfigMultiDoc:
    def test_from_list_creates_multiple_configs(self):
        configs = SwagConfig.from_list(
            [
                {"info": {"title": "API v1", "version": "1.0.0"}, "output_path": "v1.json"},
                {"info": {"title": "API v2", "version": "2.0.0"}, "output_path": "v2.json"},
            ]
        )
        assert len(configs) == 2
        assert configs[0].info["title"] == "API v1"
        assert configs[1].info["title"] == "API v2"
