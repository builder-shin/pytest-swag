from __future__ import annotations

import json
from pathlib import Path

from pytest_swag.config import SwagConfig
from pytest_swag.schema import make_openapi_skeleton


class SwagGenerator:
    def __init__(
        self,
        *,
        config: SwagConfig,
        paths: dict,
        component_schemas: dict | None = None,
        security_schemes: dict | None = None,
    ) -> None:
        self._config = config
        self._paths = paths
        self._component_schemas = component_schemas or {}
        self._security_schemes = security_schemes or {}

    def generate(self) -> dict:
        doc = make_openapi_skeleton(
            openapi=self._config.openapi,
            info=self._config.info,
            servers=self._config.servers or None,
            security=self._config.security or None,
        )
        doc["paths"] = self._convert_paths(self._paths)
        components: dict = {}
        if self._component_schemas:
            components["schemas"] = self._component_schemas
        if self._security_schemes:
            components["securitySchemes"] = self._security_schemes
        if components:
            doc["components"] = components
        return doc

    def _convert_paths(self, paths: dict) -> dict:
        converted: dict = {}
        for path, methods in paths.items():
            converted[path] = {}
            for method, operation in methods.items():
                op = dict(operation)
                if "responses" in op:
                    op["responses"] = {str(code): resp for code, resp in op["responses"].items()}
                converted[path][method] = op
        return converted

    def write(self) -> None:
        doc = self.generate()
        output_path = Path(self._config.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fmt = self._config.output_format
        if fmt in ("json", "both"):
            json_path = output_path.with_suffix(".json") if fmt == "both" else output_path
            json_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")

        if fmt in ("yaml", "both"):
            try:
                import yaml
            except ImportError as e:
                raise ImportError(
                    "PyYAML is required for YAML output. "
                    "Install it with: pip install pytest-swag[yaml]"
                ) from e
            yaml_path = output_path.with_suffix(".yaml") if fmt == "both" else output_path
            yaml_path.write_text(
                yaml.dump(doc, default_flow_style=False, allow_unicode=True, sort_keys=False)
            )

    def to_stdout(self) -> str:
        doc = self.generate()
        return json.dumps(doc, indent=2, ensure_ascii=False)
