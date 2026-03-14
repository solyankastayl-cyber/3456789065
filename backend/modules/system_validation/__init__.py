"""
PHASE 25.6 — System Validation Module

A/B/C comparison for Macro-Fractal integration validation.

System A: TA + Exchange (baseline)
System B: TA + Exchange + Fractal
System C: TA + Exchange + Fractal + Macro (full system)

Purpose: Prove that Macro-Fractal layer does NOT break core signals.
"""

from .ab_test_types import (
    SystemComparison,
    SystemComparisonSummary,
    SystemValidationHealth,
    SystemConfig,
)
from .ab_test_engine import (
    ABTestEngine,
    get_ab_test_engine,
)

__all__ = [
    "SystemComparison",
    "SystemComparisonSummary",
    "SystemValidationHealth",
    "SystemConfig",
    "ABTestEngine",
    "get_ab_test_engine",
]
