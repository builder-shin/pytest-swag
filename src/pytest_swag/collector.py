from __future__ import annotations

import warnings


class SwagCollector:
    def __init__(self) -> None:
        self._operations: list[dict] = []

    def collect(self, operation: dict) -> None:
        self._operations.append(operation)

    def get_operations(self, *, doc_target: str | None = None) -> list[dict]:
        return [
            op for op in self._operations
            if op.get("doc_target") == doc_target
        ]

    def merge_to_paths(self, *, doc_target: str | None = None) -> dict:
        paths: dict = {}
        for op in self.get_operations(doc_target=doc_target):
            path = op["path"]
            method = op["method"]
            if path not in paths:
                paths[path] = {}
            if method in paths[path]:
                existing = paths[path][method]
                for code, resp in op["responses"].items():
                    if code in existing["responses"]:
                        warnings.warn(
                            f"Conflicting schema for {method.upper()} {path} → {code}. "
                            f"Using latest definition.",
                            stacklevel=2,
                        )
                    existing["responses"][code] = resp
            else:
                method_obj: dict = {"summary": op.get("summary", "")}
                if op.get("tags"):
                    method_obj["tags"] = op["tags"]
                if op.get("parameters"):
                    method_obj["parameters"] = op["parameters"]
                if op.get("requestBody"):
                    method_obj["requestBody"] = op["requestBody"]
                method_obj["responses"] = dict(op.get("responses", {}))
                if op.get("security") is not None:
                    method_obj["security"] = op["security"]
                paths[path][method] = method_obj
        return paths
