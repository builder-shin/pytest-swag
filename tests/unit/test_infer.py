from pytest_swag.infer import infer_schema


class TestInferSchema:
    def test_string(self):
        assert infer_schema("hello") == {"type": "string"}

    def test_integer(self):
        assert infer_schema(42) == {"type": "integer"}

    def test_float(self):
        assert infer_schema(3.14) == {"type": "number"}

    def test_boolean(self):
        assert infer_schema(True) == {"type": "boolean"}

    def test_none(self):
        assert infer_schema(None) == {"nullable": True}

    def test_empty_list(self):
        assert infer_schema([]) == {"type": "array"}

    def test_list_of_strings(self):
        assert infer_schema(["a", "b"]) == {
            "type": "array",
            "items": {"type": "string"},
        }

    def test_list_of_objects(self):
        result = infer_schema([{"id": 1}, {"id": 2}])
        assert result == {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "integer"}},
            },
        }

    def test_dict(self):
        result = infer_schema({"id": 1, "name": "Alice"})
        assert result == {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
            },
        }

    def test_nested_dict(self):
        result = infer_schema({"user": {"id": 1, "active": True}})
        assert result == {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "active": {"type": "boolean"},
                    },
                },
            },
        }

    def test_dict_with_null_value(self):
        result = infer_schema({"id": 1, "deleted_at": None})
        assert result == {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "deleted_at": {"nullable": True},
            },
        }
