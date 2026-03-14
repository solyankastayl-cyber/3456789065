"""
Hypothesis Engine — Registry

PHASE 29.1 — Storage for market hypothesis history in MongoDB.

Collection: market_hypothesis_history
"""

from typing import List, Optional
from datetime import datetime
import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from .hypothesis_types import (
    MarketHypothesis,
    HypothesisHistoryRecord,
    HypothesisSummary,
)


class HypothesisRegistry:
    """
    Registry for storing market hypothesis history.

    Collection: market_hypothesis_history
    """

    COLLECTION = "market_hypothesis_history"

    def __init__(self, db=None):
        self._db = db
        self._client = None
        self._cache: List[HypothesisHistoryRecord] = []
        self._use_cache = False if db is not None else None

    async def _get_db(self):
        """Get or create database connection."""
        if self._db is not None:
            return self._db

        mongo_url = os.environ.get("MONGO_URL")
        db_name = os.environ.get("DB_NAME", "ta_engine")

        if mongo_url:
            if self._client is None:
                self._client = AsyncIOMotorClient(mongo_url)
            self._use_cache = False
            return self._client[db_name]

        self._use_cache = True
        return None

    # ═══════════════════════════════════════════════════════════
    # Write Operations
    # ═══════════════════════════════════════════════════════════

    async def store_hypothesis(
        self,
        hypothesis: MarketHypothesis,
    ) -> HypothesisHistoryRecord:
        """Store hypothesis in history."""
        record = HypothesisHistoryRecord(
            symbol=hypothesis.symbol,
            hypothesis_type=hypothesis.hypothesis_type,
            directional_bias=hypothesis.directional_bias,
            confidence=hypothesis.confidence,
            reliability=hypothesis.reliability,
            execution_state=hypothesis.execution_state,
            created_at=datetime.utcnow(),
        )

        db = await self._get_db()
        if self._use_cache:
            self._cache.append(record)
        else:
            if db is not None:
                await db[self.COLLECTION].insert_one(record.model_dump())

        return record

    # ═══════════════════════════════════════════════════════════
    # Read Operations
    # ═══════════════════════════════════════════════════════════

    async def get_history(
        self,
        symbol: str,
        limit: int = 100,
    ) -> List[HypothesisHistoryRecord]:
        """Get hypothesis history for symbol."""
        db = await self._get_db()
        if self._use_cache:
            history = [r for r in self._cache if r.symbol == symbol]
            return sorted(history, key=lambda r: r.created_at, reverse=True)[:limit]

        if db is None:
            return []

        cursor = db[self.COLLECTION].find(
            {"symbol": symbol}
        ).sort("created_at", -1).limit(limit)

        results = []
        async for doc in cursor:
            doc.pop("_id", None)
            results.append(HypothesisHistoryRecord(**doc))

        return results

    async def get_latest(
        self,
        symbol: str,
    ) -> Optional[HypothesisHistoryRecord]:
        """Get most recent hypothesis for symbol."""
        history = await self.get_history(symbol, limit=1)
        return history[0] if history else None

    # ═══════════════════════════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════════════════════════

    async def get_summary(
        self,
        symbol: str,
    ) -> HypothesisSummary:
        """Get summary statistics for symbol."""
        history = await self.get_history(symbol, limit=100)

        if not history:
            return HypothesisSummary(
                symbol=symbol,
                total_records=0,
            )

        # Type counts
        type_map = {
            "BULLISH_CONTINUATION": 0,
            "BEARISH_CONTINUATION": 0,
            "BREAKOUT_FORMING": 0,
            "RANGE_MEAN_REVERSION": 0,
            "NO_EDGE": 0,
        }
        other_count = 0
        for r in history:
            if r.hypothesis_type in type_map:
                type_map[r.hypothesis_type] += 1
            else:
                other_count += 1

        # Bias counts
        long_c = len([r for r in history if r.directional_bias == "LONG"])
        short_c = len([r for r in history if r.directional_bias == "SHORT"])
        neutral_c = len([r for r in history if r.directional_bias == "NEUTRAL"])

        # Execution state counts
        favorable_c = len([r for r in history if r.execution_state == "FAVORABLE"])
        cautious_c = len([r for r in history if r.execution_state == "CAUTIOUS"])
        unfavorable_c = len([r for r in history if r.execution_state == "UNFAVORABLE"])

        # Averages
        avg_conf = sum(r.confidence for r in history) / len(history)
        avg_rel = sum(r.reliability for r in history) / len(history)

        return HypothesisSummary(
            symbol=symbol,
            total_records=len(history),
            bullish_continuation_count=type_map["BULLISH_CONTINUATION"],
            bearish_continuation_count=type_map["BEARISH_CONTINUATION"],
            breakout_forming_count=type_map["BREAKOUT_FORMING"],
            range_mean_reversion_count=type_map["RANGE_MEAN_REVERSION"],
            no_edge_count=type_map["NO_EDGE"],
            other_count=other_count,
            long_count=long_c,
            short_count=short_c,
            neutral_count=neutral_c,
            favorable_count=favorable_c,
            cautious_count=cautious_c,
            unfavorable_count=unfavorable_c,
            average_confidence=round(avg_conf, 4),
            average_reliability=round(avg_rel, 4),
            current_hypothesis=history[0].hypothesis_type,
            current_bias=history[0].directional_bias,
        )

    # ═══════════════════════════════════════════════════════════
    # Utilities
    # ═══════════════════════════════════════════════════════════

    async def clear_history(self, symbol: Optional[str] = None) -> None:
        """Clear hypothesis history (for testing)."""
        db = await self._get_db()
        if self._use_cache:
            if symbol:
                self._cache = [r for r in self._cache if r.symbol != symbol]
            else:
                self._cache.clear()
        else:
            if db is not None:
                if symbol:
                    await db[self.COLLECTION].delete_many({"symbol": symbol})
                else:
                    await db[self.COLLECTION].delete_many({})


# Singleton
_registry: Optional[HypothesisRegistry] = None


def get_hypothesis_registry() -> HypothesisRegistry:
    """Get singleton instance of HypothesisRegistry."""
    global _registry
    if _registry is None:
        _registry = HypothesisRegistry()
    return _registry
