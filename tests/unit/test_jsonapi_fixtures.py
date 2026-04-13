def test_swag_jsonapi_fixture_exists(pytester):
    pytester.makeconftest("""
        import pytest

        @pytest.fixture(scope="session")
        def swag_config():
            return {
                "openapi": "3.0.3",
                "info": {"title": "Test", "version": "1.0"},
            }
    """)
    pytester.makepyfile("""
        def test_fixture_available(swag_jsonapi):
            assert swag_jsonapi is not None
            assert hasattr(swag_jsonapi, 'jsonapi_resource')
            assert hasattr(swag_jsonapi, 'jsonapi_response')
    """)
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=1)


def test_swag_jsonapi_requests_fixture_exists(pytester):
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
        def test_fixture_available(swag_jsonapi_requests):
            assert swag_jsonapi_requests is not None
            assert hasattr(swag_jsonapi_requests, 'jsonapi_resource')
            assert hasattr(swag_jsonapi_requests, 'run_test')
    """)
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=1)
