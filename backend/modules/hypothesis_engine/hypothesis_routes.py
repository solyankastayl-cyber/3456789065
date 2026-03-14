"""
Hypothesis Engine — Routes

PHASE 29.1 — API endpoints for market hypothesis.

Endpoints:
- GET  /api/v1/hypothesis/current/{symbol}
- GET  /api/v1/hypothesis/history/{symbol}
- GET  /api/v1/hypothesis/summary/{symbol}
- POST /api/v1/hypothesis/recompute/{symbol}
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime, timezone

from .hypothesis_engine import (
    HypothesisEngine,
    get_hypothesis_engine,
)
from .hypothesis_registry import (
    HypothesisRegistry,
    get_hypothesis_registry,
)


router = APIRouter(prefix="/api/v1/hypothesis", tags=["hypothesis"])


@router.get("/current/{symbol}", response_model=Dict[str, Any])
async def get_current_hypothesis(symbol: str):
    """
    Get current market hypothesis for symbol.

    Generates hypothesis from intelligence layers if not cached.
    
    PHASE 29.2: Returns new scoring components:
    - structural_score
    - execution_score
    - conflict_score
    
    PHASE 29.3: Returns conflict_state (LOW/MODERATE/HIGH)
    """
    engine = get_hypothesis_engine()

    # Build hypothesis
    hypothesis = engine.generate_hypothesis_simulated(symbol.upper())

    # Store in registry
    registry = get_hypothesis_registry()
    await registry.store_hypothesis(hypothesis)

    return {
        "symbol": hypothesis.symbol,
        "hypothesis_type": hypothesis.hypothesis_type,
        "directional_bias": hypothesis.directional_bias,
        # PHASE 29.2 scores
        "structural_score": hypothesis.structural_score,
        "execution_score": hypothesis.execution_score,
        "conflict_score": hypothesis.conflict_score,
        # PHASE 29.3 conflict state
        "conflict_state": hypothesis.conflict_state,
        # Derived (adjusted by conflict resolver)
        "confidence": hypothesis.confidence,
        "reliability": hypothesis.reliability,
        # Support layers
        "alpha_support": hypothesis.alpha_support,
        "regime_support": hypothesis.regime_support,
        "microstructure_support": hypothesis.microstructure_support,
        "macro_fractal_support": hypothesis.macro_fractal_support,
        # Execution (adjusted by conflict resolver)
        "execution_state": hypothesis.execution_state,
        "reason": hypothesis.reason,
        "created_at": hypothesis.created_at.isoformat(),
    }


@router.get("/history/{symbol}", response_model=Dict[str, Any])
async def get_hypothesis_history(symbol: str, limit: int = 50):
    """
    Get hypothesis history for symbol.
    """
    registry = get_hypothesis_registry()
    history = await registry.get_history(symbol.upper(), limit=limit)

    return {
        "symbol": symbol.upper(),
        "total": len(history),
        "records": [
            {
                "hypothesis_type": r.hypothesis_type,
                "directional_bias": r.directional_bias,
                "confidence": r.confidence,
                "reliability": r.reliability,
                "execution_state": r.execution_state,
                "created_at": r.created_at.isoformat(),
            }
            for r in history
        ],
    }


@router.get("/summary/{symbol}", response_model=Dict[str, Any])
async def get_hypothesis_summary(symbol: str):
    """
    Get hypothesis summary statistics for symbol.
    """
    engine = get_hypothesis_engine()

    # Ensure at least one hypothesis exists
    if not engine.get_hypothesis(symbol.upper()):
        engine.generate_hypothesis_simulated(symbol.upper())

    summary = engine.get_summary(symbol.upper())

    return {
        "symbol": summary.symbol,
        "total_records": summary.total_records,
        "types": {
            "bullish_continuation": summary.bullish_continuation_count,
            "bearish_continuation": summary.bearish_continuation_count,
            "breakout_forming": summary.breakout_forming_count,
            "range_mean_reversion": summary.range_mean_reversion_count,
            "no_edge": summary.no_edge_count,
            "other": summary.other_count,
        },
        "bias": {
            "long": summary.long_count,
            "short": summary.short_count,
            "neutral": summary.neutral_count,
        },
        "execution_states": {
            "favorable": summary.favorable_count,
            "cautious": summary.cautious_count,
            "unfavorable": summary.unfavorable_count,
        },
        "averages": {
            "confidence": summary.average_confidence,
            "reliability": summary.average_reliability,
        },
        "current": {
            "hypothesis": summary.current_hypothesis,
            "bias": summary.current_bias,
        },
    }


@router.post("/recompute/{symbol}", response_model=Dict[str, Any])
async def recompute_hypothesis(symbol: str):
    """
    Force recompute of market hypothesis.

    Regenerates hypothesis from all intelligence layers.
    
    PHASE 29.2: Returns new scoring components.
    PHASE 29.3: Returns conflict_state.
    """
    try:
        engine = get_hypothesis_engine()

        # Recompute
        hypothesis = engine.generate_hypothesis_simulated(symbol.upper())

        # Store in registry
        registry = get_hypothesis_registry()
        await registry.store_hypothesis(hypothesis)

        return {
            "status": "ok",
            "symbol": hypothesis.symbol,
            "hypothesis_type": hypothesis.hypothesis_type,
            "directional_bias": hypothesis.directional_bias,
            # PHASE 29.2 scores
            "structural_score": hypothesis.structural_score,
            "execution_score": hypothesis.execution_score,
            "conflict_score": hypothesis.conflict_score,
            # PHASE 29.3 conflict state
            "conflict_state": hypothesis.conflict_state,
            # Derived (adjusted)
            "confidence": hypothesis.confidence,
            "reliability": hypothesis.reliability,
            # Support layers
            "alpha_support": hypothesis.alpha_support,
            "regime_support": hypothesis.regime_support,
            "microstructure_support": hypothesis.microstructure_support,
            "macro_fractal_support": hypothesis.macro_fractal_support,
            # Execution (adjusted)
            "execution_state": hypothesis.execution_state,
            "reason": hypothesis.reason,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Recompute failed: {str(e)}",
        )
