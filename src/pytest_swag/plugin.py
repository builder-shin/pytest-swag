from __future__ import annotations

import pytest

from pytest_swag.builder import SwagBuilder
from pytest_swag.collector import SwagCollector
from pytest_swag.config import SwagConfig
from pytest_swag.generator import SwagGenerator
from pytest_swag.validator import SwagValidator

_swag_config_key = pytest.StashKey[dict | list[dict]]()
_swag_schemas_key = pytest.StashKey[dict]()
_swag_security_key = pytest.StashKey[dict]()
_swag_collector_key = pytest.StashKey[SwagCollector]()


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("swag", "OpenAPI documentation generation")
    group.addoption(
        "--swag", action="store_true", default=False, help="Generate OpenAPI documentation"
    )
    group.addoption("--swag-output", default=None, help="Override output path")
    group.addoption("--swag-no-output", action="store_true", default=False, help="Skip file output")
    group.addoption(
        "--swag-dry-run", action="store_true", default=False, help="Print OpenAPI doc to stdout"
    )
    group.addoption(
        "--swag-strict", action="store_true", default=False, help="Warn on unvalidated tests"
    )


def pytest_configure(config: pytest.Config) -> None:
    config.stash[_swag_collector_key] = SwagCollector()


@pytest.fixture(scope="session")
def swag_config() -> dict | list[dict]:
    return {}


@pytest.fixture(scope="session")
def swag_schemas() -> dict:
    return {}


@pytest.fixture(scope="session")
def swag_security_schemes() -> dict:
    return {}


@pytest.fixture(scope="session", autouse=True)
def _swag_store_config(request, swag_config, swag_schemas, swag_security_schemes):
    request.config.stash[_swag_config_key] = swag_config
    request.config.stash[_swag_schemas_key] = swag_schemas
    request.config.stash[_swag_security_key] = swag_security_schemes


def _make_validate(builder: SwagBuilder, component_schemas: dict):
    def validate(status_code: int, body: object = None) -> None:
        if builder._captured:
            from pytest_swag.builder import SwagBuildError

            raise SwagBuildError("Cannot mix capture() and validate() in the same test")
        validator = SwagValidator(
            responses=builder._responses,
            path=builder._path,
            method=builder._method,
            component_schemas=component_schemas,
        )
        validator.validate(status_code, body)
        builder._validated = True

    return validate


@pytest.fixture
def swag(request, swag_schemas):
    builder = SwagBuilder()
    builder.validate = _make_validate(builder, swag_schemas)
    yield builder
    if not builder._validated:
        if request.config.getoption("--swag-strict", default=False):
            import warnings

            warnings.warn(
                f"Test {request.node.nodeid} uses swag fixture but never called validate()",
                stacklevel=2,
            )
        return
    op = builder.to_operation_dict()
    if builder._doc_target is not None:
        op["doc_target"] = builder._doc_target
    collector = request.config.stash[_swag_collector_key]
    collector.collect(op)


@pytest.fixture
def swag_requests(request, swag_schemas):
    from pytest_swag.adapters.requests import RequestsSwagBuilder

    builder = RequestsSwagBuilder()
    builder.validate = _make_validate(builder, swag_schemas)
    original_validate_response = builder.validate_response

    def _validate_response(response, *, component_schemas=None):
        original_validate_response(response, component_schemas=component_schemas or swag_schemas)

    builder.validate_response = _validate_response
    yield builder
    if not builder._validated:
        if request.config.getoption("--swag-strict", default=False):
            import warnings

            warnings.warn(
                f"Test {request.node.nodeid} uses swag_requests fixture but never called validate_response()",
                stacklevel=2,
            )
        return
    op = builder.to_operation_dict()
    if builder._doc_target is not None:
        op["doc_target"] = builder._doc_target
    collector = request.config.stash[_swag_collector_key]
    collector.collect(op)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    config = session.config
    if not config.getoption("--swag", default=False):
        return

    raw_config = config.stash.get(_swag_config_key, {})
    raw_schemas = config.stash.get(_swag_schemas_key, {})
    raw_security = config.stash.get(_swag_security_key, {})
    collector = config.stash.get(_swag_collector_key, SwagCollector())

    if config.getoption("--swag-no-output", default=False):
        return

    if isinstance(raw_config, list):
        configs = SwagConfig.from_list(raw_config)
    else:
        configs = [SwagConfig.from_dict(raw_config)]

    output_override = config.getoption("--swag-output", default=None)
    dry_run = config.getoption("--swag-dry-run", default=False)

    for swag_config in configs:
        if output_override and len(configs) == 1:
            swag_config.output_path = output_override

        doc_target = swag_config.info.get("title") if len(configs) > 1 else None
        paths = collector.merge_to_paths(doc_target=doc_target)

        gen = SwagGenerator(
            config=swag_config,
            paths=paths,
            component_schemas=raw_schemas,
            security_schemes=raw_security,
        )

        if dry_run:
            print(gen.to_stdout())
        else:
            gen.write()
