import json


def test_swag_fixture_available(pytester):
    pytester.makepyfile("""
        def test_has_swag(swag):
            assert swag is not None
    """)
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_swag_generates_openapi_json(pytester, tmp_path):
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "openapi": "3.1.0",
                "info": {{"title": "Test API", "version": "1.0.0"}},
                "output_path": "{output}",
                "output_format": "json",
            }}
    """)
    pytester.makepyfile("""
        def test_get_blogs(swag):
            swag.path("/blogs").get("List blogs")
            swag.response(200, description="OK", schema={
                "type": "array",
                "items": {"type": "object"},
            })
            swag.validate(200, [{"id": 1}])
    """)
    result = pytester.runpytest("--swag")
    result.assert_outcomes(passed=1)
    assert output.exists()
    data = json.loads(output.read_text())
    assert data["openapi"] == "3.1.0"
    assert "/blogs" in data["paths"]


def test_no_output_without_swag_flag(pytester, tmp_path):
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "output_path": "{output}",
            }}
    """)
    pytester.makepyfile("""
        def test_get_blogs(swag):
            swag.path("/blogs").get("List blogs")
            swag.response(200, schema={"type": "array"})
            swag.validate(200, [])
    """)
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
    assert not output.exists()


def test_validation_failure_fails_test(pytester):
    pytester.makepyfile("""
        def test_wrong_type(swag):
            swag.path("/blogs").get("List blogs")
            swag.response(200, schema={
                "type": "object",
                "required": ["id"],
                "properties": {"id": {"type": "integer"}},
            })
            swag.validate(200, {"id": "not_an_int"})
    """)
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*SwagValidationError*"])


def test_undocumented_status_code_fails_test(pytester):
    pytester.makepyfile("""
        def test_undocumented(swag):
            swag.path("/blogs").get("List blogs")
            swag.response(200, schema={"type": "array"})
            swag.validate(404, {})
    """)
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*Undocumented status code*"])


def test_failed_test_excluded_from_output(pytester, tmp_path):
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "output_path": "{output}",
            }}
    """)
    pytester.makepyfile("""
        def test_valid(swag):
            swag.path("/valid").get("Valid endpoint")
            swag.response(200, schema={"type": "object"})
            swag.validate(200, {})

        def test_invalid(swag):
            swag.path("/invalid").get("Invalid endpoint")
            swag.response(200, schema={"type": "object", "required": ["id"], "properties": {"id": {"type": "integer"}}})
            swag.validate(200, {"id": "wrong"})
    """)
    result = pytester.runpytest("--swag")
    result.assert_outcomes(passed=1, failed=1)
    data = json.loads(output.read_text())
    assert "/valid" in data["paths"]
    assert "/invalid" not in data["paths"]


def test_ref_schema_validation(pytester, tmp_path):
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "output_path": "{output}",
            }}

        @pytest.fixture(scope="session")
        def swag_schemas():
            return {{
                "Blog": {{
                    "type": "object",
                    "required": ["id"],
                    "properties": {{"id": {{"type": "integer"}}}},
                }}
            }}
    """)
    pytester.makepyfile("""
        def test_get_blog(swag):
            swag.path("/blogs/{id}").get("Get blog")
            swag.parameter("id", in_="path", schema={"type": "string"})
            swag.response(200, schema={"$ref": "#/components/schemas/Blog"})
            swag.validate(200, {"id": 1})
    """)
    result = pytester.runpytest("--swag")
    result.assert_outcomes(passed=1)
    data = json.loads(output.read_text())
    assert data["components"]["schemas"]["Blog"]["type"] == "object"


def test_security_scheme_in_output(pytester, tmp_path):
    output = tmp_path / "openapi.json"
    pytester.makeconftest(f"""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {{
                "output_path": "{output}",
            }}

        @pytest.fixture(scope="session")
        def swag_security_schemes():
            return {{
                "BearerAuth": {{
                    "type": "http",
                    "scheme": "bearer",
                }}
            }}
    """)
    pytester.makepyfile("""
        def test_secured(swag):
            swag.path("/admin").get("Admin")
            swag.security("BearerAuth")
            swag.response(200, schema={"type": "object"})
            swag.validate(200, {})
    """)
    result = pytester.runpytest("--swag")
    result.assert_outcomes(passed=1)
    data = json.loads(output.read_text())
    assert "BearerAuth" in data["components"]["securitySchemes"]


def test_dry_run_outputs_to_stdout(pytester):
    pytester.makepyfile("""
        def test_blog(swag):
            swag.path("/blogs").get("List")
            swag.response(200, schema={"type": "array"})
            swag.validate(200, [])
    """)
    result = pytester.runpytest("--swag", "--swag-dry-run")
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(['*"openapi"*'])
