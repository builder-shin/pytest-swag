from __future__ import annotations


class JsonApiValidationError(Exception):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("\n".join(errors))


class JsonApiResponseValidator:
    @staticmethod
    def validate_compound_document(body: dict) -> list[str]:
        errors: list[str] = []
        included = body.get("included")
        if included is None:
            return errors

        seen: set[tuple[str, str]] = set()
        for i, item in enumerate(included):
            if "type" not in item:
                errors.append(f"included[{i}]: missing 'type' field")
            if "id" not in item:
                errors.append(f"included[{i}]: missing 'id' field")
            if "type" in item and "id" in item:
                key = (item["type"], item["id"])
                if key in seen:
                    errors.append(
                        f"included: duplicate resource ({item['type']}, {item['id']})"
                    )
                seen.add(key)

        data = body.get("data")
        referenced: set[tuple[str, str]] = set()
        if data is not None:
            resources = data if isinstance(data, list) else [data]
            for resource in resources:
                _collect_linkages(resource, referenced)

        for ref in referenced:
            if ref not in seen:
                errors.append(
                    f"included: missing resource ({ref[0]}, {ref[1]}) "
                    f"referenced in relationships"
                )

        for key in seen:
            if key not in referenced:
                errors.append(
                    f"included: orphan resource ({key[0]}, {key[1]}) "
                    f"not referenced by any relationship"
                )

        return errors

    @staticmethod
    def validate_jsonapi_member(body: dict) -> list[str]:
        errors: list[str] = []
        jsonapi = body.get("jsonapi")
        if jsonapi is None:
            return errors

        if not isinstance(jsonapi, dict):
            errors.append("'jsonapi' member must be an object")
            return errors

        version = jsonapi.get("version")
        if version is not None and not isinstance(version, str):
            errors.append("'jsonapi.version' must be a string")

        return errors


def _collect_linkages(
    resource: dict, referenced: set[tuple[str, str]]
) -> None:
    relationships = resource.get("relationships")
    if not relationships:
        return
    for rel_data in relationships.values():
        if not isinstance(rel_data, dict):
            continue
        data = rel_data.get("data")
        if data is None:
            continue
        if isinstance(data, list):
            for item in data:
                if "type" in item and "id" in item:
                    referenced.add((item["type"], item["id"]))
        elif isinstance(data, dict):
            if "type" in data and "id" in data:
                referenced.add((data["type"], data["id"]))
