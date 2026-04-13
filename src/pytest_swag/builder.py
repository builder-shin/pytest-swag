from __future__ import annotations

from http import HTTPStatus


class SwagBuildError(Exception):
    pass


class _PathProxy:
    def __init__(self, builder: SwagBuilder, path: str) -> None:
        self._builder = builder
        self._builder._path = path

    def _set_method(self, method: str, summary: str) -> SwagBuilder:
        self._builder._method = method
        self._builder._summary = summary
        return self._builder

    def get(self, summary: str = "") -> SwagBuilder:
        return self._set_method("get", summary)

    def post(self, summary: str = "") -> SwagBuilder:
        return self._set_method("post", summary)

    def put(self, summary: str = "") -> SwagBuilder:
        return self._set_method("put", summary)

    def patch(self, summary: str = "") -> SwagBuilder:
        return self._set_method("patch", summary)

    def delete(self, summary: str = "") -> SwagBuilder:
        return self._set_method("delete", summary)


class SwagBuilder:
    def __init__(self) -> None:
        self._path: str | None = None
        self._method: str | None = None
        self._summary: str = ""
        self._tags: list[str] = []
        self._parameters: list[dict] = []
        self._request_body: dict | None = None
        self._responses: dict[int, dict] = {}
        self._security: list[dict] | None = None
        self._doc_target: str | None = None
        self._validated: bool = False
        self._captured: bool = False

    def path(self, path: str) -> _PathProxy:
        return _PathProxy(self, path)

    def tag(self, name: str) -> SwagBuilder:
        self._tags.append(name)
        return self

    def parameter(
        self,
        name: str,
        *,
        in_: str,
        schema: dict,
        required: bool | None = None,
        value: object = None,
    ) -> SwagBuilder:
        if in_ == "path":
            required = True
        elif required is None:
            required = False
        param = {
            "name": name,
            "in": in_,
            "required": required,
            "schema": schema,
        }
        if value is not None:
            param["value"] = value
        self._parameters.append(param)
        return self

    def request_body(
        self,
        *,
        content_type: str = "application/json",
        schema: dict,
    ) -> SwagBuilder:
        self._request_body = {
            "content": {
                content_type: {"schema": schema},
            },
        }
        return self

    def response(
        self,
        status_code: int,
        *,
        description: str | None = None,
        schema: dict | None = None,
    ) -> SwagBuilder:
        if description is None:
            try:
                description = HTTPStatus(status_code).phrase
            except ValueError:
                description = ""
        self._responses[status_code] = {
            "description": description,
            "schema": schema,
        }
        return self

    def capture(
        self,
        status_code: int,
        body: object = None,
        *,
        description: str | None = None,
        infer_schema: bool = True,
    ) -> SwagBuilder:
        if self._validated and not self._captured:
            raise SwagBuildError("Cannot mix capture() and validate() in the same test")
        if description is None:
            try:
                description = HTTPStatus(status_code).phrase
            except ValueError:
                description = ""
        schema = None
        if body is not None and infer_schema:
            from pytest_swag.infer import infer_schema as _infer

            schema = _infer(body)
        self._responses[status_code] = {
            "description": description,
            "schema": schema,
            "example": body,
        }
        self._validated = True
        self._captured = True
        return self

    def security(self, scheme: str | None) -> SwagBuilder:
        if self._security is None:
            self._security = []
        if scheme is None:
            self._security = []
        else:
            self._security.append({scheme: []})
        return self

    def doc(self, target: str) -> SwagBuilder:
        self._doc_target = target
        return self

    def to_operation_dict(self) -> dict:
        op: dict = {
            "path": self._path,
            "method": self._method,
            "summary": self._summary,
        }
        if self._tags:
            op["tags"] = self._tags
        if self._parameters:
            op["parameters"] = [
                {k: v for k, v in p.items() if k != "value"} for p in self._parameters
            ]
        if self._request_body:
            op["requestBody"] = self._request_body
        responses: dict[int, dict] = {}
        for code, resp in self._responses.items():
            entry: dict = {"description": resp["description"]}
            has_schema = resp.get("schema") is not None
            has_example = resp.get("example") is not None
            if has_schema or has_example:
                media: dict = {}
                if has_schema:
                    media["schema"] = resp["schema"]
                if has_example:
                    media["example"] = resp["example"]
                entry["content"] = {"application/json": media}
            responses[code] = entry
        op["responses"] = responses
        if self._security is not None:
            op["security"] = self._security
        return op
