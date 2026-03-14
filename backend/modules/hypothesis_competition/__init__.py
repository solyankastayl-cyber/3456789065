"""
Hypothesis Competition

PHASE 30.1 — Hypothesis Pool Engine

Transforms system from single-hypothesis to multi-hypothesis mode.
"""

from .hypothesis_pool_engine import (
    HypothesisPoolEngine,
    get_hypothesis_pool_engine,
)
from .hypothesis_pool_registry import (
    HypothesisPoolRegistry,
    get_hypothesis_pool_registry,
)
from .hypothesis_pool_routes import router as hypothesis_pool_router
from .hypothesis_pool_types import (
    HypothesisPoolItem,
    HypothesisPool,
    HypothesisPoolSummary,
    HypothesisPoolHistoryRecord,
    CONFIDENCE_THRESHOLD,
    RELIABILITY_THRESHOLD,
    MAX_POOL_SIZE,
)

__all__ = [
    "HypothesisPoolEngine",
    "get_hypothesis_pool_engine",
    "HypothesisPoolRegistry",
    "get_hypothesis_pool_registry",
    "hypothesis_pool_router",
    "HypothesisPoolItem",
    "HypothesisPool",
    "HypothesisPoolSummary",
    "HypothesisPoolHistoryRecord",
    "CONFIDENCE_THRESHOLD",
    "RELIABILITY_THRESHOLD",
    "MAX_POOL_SIZE",
]
