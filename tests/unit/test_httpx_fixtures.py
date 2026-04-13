def test_swag_httpx_fixture_exists(pytester):
    pytester.makeconftest("""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {
                "openapi": "3.0.3",
                "info": {"title": "Test", "version": "1.0"},
                "servers": [{"url": "http://localhost:8000"}],
            }
    """)
    pytester.makepyfile("""
        def test_fixture_available(swag_httpx):
            assert swag_httpx is not None
            assert hasattr(swag_httpx, 'run_test')
            assert hasattr(swag_httpx, 'validate_response')
    """)
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=1)


def test_swag_jsonapi_httpx_fixture_exists(pytester):
    pytester.makeconftest("""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {
                "openapi": "3.0.3",
                "info": {"title": "Test", "version": "1.0"},
                "servers": [{"url": "http://localhost:8000"}],
            }
    """)
    pytester.makepyfile("""
        def test_fixture_available(swag_jsonapi_httpx):
            assert swag_jsonapi_httpx is not None
            assert hasattr(swag_jsonapi_httpx, 'jsonapi_resource')
            assert hasattr(swag_jsonapi_httpx, 'jsonapi_include')
            assert hasattr(swag_jsonapi_httpx, 'run_test')
    """)
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=1)
