from __future__ import annotations

from dataclasses import dataclass


@dataclass
class JsonApiQuery:
    fields: dict[str, list[str]] | None = None
    include: list[str] | None = None
    filter: dict[str, str | dict[str, str]] | None = None
    sort: list[str] | None = None
    page: dict[str, int] | None = None

    def to_query_params(self) -> dict[str, str]:
        params: dict[str, str] = {}

        if self.fields:
            for type_name, field_list in self.fields.items():
                params[f"fields[{type_name}]"] = ",".join(field_list)

        if self.include:
            params["include"] = ",".join(self.include)

        if self.filter:
            for field, value in self.filter.items():
                if isinstance(value, dict):
                    for op, op_value in value.items():
                        params[f"filter[{field}][{op}]"] = str(op_value)
                else:
                    params[f"filter[{field}]"] = str(value)

        if self.sort:
            params["sort"] = ",".join(self.sort)

        if self.page:
            for key, value in self.page.items():
                params[f"page[{key}]"] = str(value)

        return params
