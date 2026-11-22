"""Exact randomization tests for matched binary outcomes."""

from .core import (
    Block,
    DistributionResult,
    TestResult,
    exact_null_distribution,
    plot_null_distribution,
    randomization_test,
    validate_blocks,
)

__all__ = [
    "Block",
    "DistributionResult",
    "TestResult",
    "validate_blocks",
    "exact_null_distribution",
    "randomization_test",
    "plot_null_distribution",
]
