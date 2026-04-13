"""pytest-swag: Generate OpenAPI documentation from pytest tests."""

__version__ = "0.1.0"

from pytest_swag.builder import SwagBuilder
from pytest_swag.validator import SwagValidationError

__all__ = ["SwagBuilder", "SwagValidationError"]
