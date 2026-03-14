"""
Hypothesis Competition

PHASE 30.1 — Hypothesis Pool Engine
PHASE 30.2 — Hypothesis Ranking Engine

Transforms system from single-hypothesis to multi-hypothesis mode
with diversification logic.
"""

from .hypothesis_pool_engine import (
    HypothesisPoolEngine,
    get_hypothesis_pool_engine,
)
from .hypothesis_ranking_engine import (
    HypothesisRankingEngine,
    get_hypothesis_ranking_engine,
    RankedHypothesisPool,
)
from .hypothesis_pool_registry import (
    HypothesisPoolRegistry,
    get_hypothesis_pool_registry,
)
from .hypothesis_pool_routes import router as hypothesis_pool_router
from .hypothesis_ranking_routes import router as hypothesis_ranking_router
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
    "HypothesisRankingEngine",
    "get_hypothesis_ranking_engine",
    "RankedHypothesisPool",
    "HypothesisPoolRegistry",
    "get_hypothesis_pool_registry",
    "hypothesis_pool_router",
    "hypothesis_ranking_router",
    "HypothesisPoolItem",
    "HypothesisPool",
    "HypothesisPoolSummary",
    "HypothesisPoolHistoryRecord",
    "CONFIDENCE_THRESHOLD",
    "RELIABILITY_THRESHOLD",
    "MAX_POOL_SIZE",
]
