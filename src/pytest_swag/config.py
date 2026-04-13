from __future__ import annotations

import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]
from dataclasses import dataclass, field
from pathlib import Path


_DEFAULTS = {
    "openapi": "3.1.0",
    "info": {"title": "API", "version": "0.1.0"},
    "output_path": "openapi.json",
    "output_format": "json",
    "servers": [],
    "security": [],
}


@dataclass
class SwagConfig:
    openapi: str = _DEFAULTS["openapi"]
    info: dict = field(default_factory=lambda: dict(_DEFAULTS["info"]))
    output_path: str = _DEFAULTS["output_path"]
    output_format: str = _DEFAULTS["output_format"]
    servers: list[dict] = field(default_factory=list)
    security: list[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> SwagConfig:
        return cls(
            openapi=data.get("openapi", _DEFAULTS["openapi"]),
            info=data.get("info", dict(_DEFAULTS["info"])),
            output_path=data.get("output_path", _DEFAULTS["output_path"]),
            output_format=data.get("output_format", _DEFAULTS["output_format"]),
            servers=data.get("servers", []),
            security=data.get("security", []),
        )

    @classmethod
    def from_pyproject(cls, root: Path) -> SwagConfig:
        pyproject_path = root / "pyproject.toml"
        if not pyproject_path.exists():
            return cls()
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        section = data.get("tool", {}).get("pytest-swag", {})
        if not section:
            return cls()
        info = section.pop("info", None)
        result = dict(section)
        if info:
            result["info"] = info
        return cls.from_dict(result)

    @classmethod
    def from_list(cls, items: list[dict]) -> list[SwagConfig]:
        return [cls.from_dict(item) for item in items]
