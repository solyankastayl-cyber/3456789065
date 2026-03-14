"""
PHASE 19.1 & 19.2 & 19.3 & 19.4 — Strategy Brain Routes
======================================================
API endpoints for Strategy Brain module.

PHASE 19.1 Endpoints:
- GET /api/v1/strategy-brain/health
- GET /api/v1/strategy-brain/registry
- GET /api/v1/strategy-brain/state
- GET /api/v1/strategy-brain/state/{strategy}
- GET /api/v1/strategy-brain/summary

PHASE 19.2 Endpoints:
- GET /api/v1/strategy-brain/allocation
- GET /api/v1/strategy-brain/allocation/{strategy}
- GET /api/v1/strategy-brain/allocation/summary

PHASE 19.3 Endpoints:
- GET /api/v1/strategy-brain/regime
- GET /api/v1/strategy-brain/regime/priority
- GET /api/v1/strategy-brain/regime/{symbol}

PHASE 19.4 Endpoints:
- GET /api/v1/strategy-brain/aggregate
- GET /api/v1/strategy-brain/aggregate/summary
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone

from modules.strategy_brain.strategy_state_engine import get_strategy_state_engine
from modules.strategy_brain.strategy_registry import (
    STRATEGY_REGISTRY,
    get_registry_summary,
    get_all_strategies,
)
from modules.strategy_brain.strategy_types import (
    StrategyType,
    StrategyStateEnum,
    STATE_THRESHOLDS,
    STATE_MODIFIERS,
)
from modules.strategy_brain.allocation import (
    get_allocation_engine,
    BASE_WEIGHTS,
    STATE_MULTIPLIERS as ALLOC_STATE_MULTIPLIERS,
)
from modules.strategy_brain.regime_switch import (
    get_regime_switch_engine,
    get_regime_map_summary,
    REGIME_STRATEGY_MAP,
    PRIORITY_MODIFIERS,
)
from modules.strategy_brain.aggregator import (
    get_strategy_brain_aggregator,
    StrategyOverlayEffect,
    RecommendedBias,
)


router = APIRouter(
    prefix="/api/v1/strategy-brain",
    tags=["Strategy Brain"]
)


# ══════════════════════════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════════════════════════

@router.get("/health")
async def strategy_brain_health():
    """Strategy Brain health check."""
    try:
        state_engine = get_strategy_state_engine()
        alloc_engine = get_allocation_engine()
        regime_engine = get_regime_switch_engine()
        aggregator = get_strategy_brain_aggregator()
        
        # Quick tests
        test_state = state_engine.compute_strategy_state("trend_following", "BTC")
        test_alloc = alloc_engine.compute_allocation("trend_following", "BTC")
        test_regime = regime_engine.compute_regime_priority("BTC")
        test_aggregate = aggregator.compute_aggregate("BTC")
        
        return {
            "status": "healthy",
            "phase": "19.4",
            "module": "Strategy Brain",
            "description": "Complete strategy-level management with aggregation",
            "capabilities": [
                "Strategy Suitability Scoring",
                "Strategy State Management",
                "Regime-based Strategy Selection",
                "Modifier Calculation",
                "Capital Allocation",
                "Weight Renormalization",
                "Regime Switch Detection",
                "Primary Strategy Selection",
                "Strategy Brain Aggregation",
                "Trading Product Overlay",
            ],
            "strategy_count": len(STRATEGY_REGISTRY),
            "regime_count": len(REGIME_STRATEGY_MAP),
            "overlay_effects": [e.value for e in StrategyOverlayEffect],
            "recommended_biases": [b.value for b in RecommendedBias],
            "test_result": {
                "strategy": test_state.strategy_name,
                "state": test_state.strategy_state.value,
                "suitability": round(test_state.suitability_score, 4),
                "capital_share": round(test_alloc.capital_share, 4),
                "regime": test_regime.market_regime,
                "primary_strategy": test_regime.primary_strategy,
                "overlay_effect": test_aggregate.strategy_overlay_effect.value,
                "recommended_bias": test_aggregate.recommended_bias.value,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ══════════════════════════════════════════════════════════════
# REGISTRY ENDPOINT
# ══════════════════════════════════════════════════════════════

@router.get("/registry")
async def get_strategy_registry():
    """
    Get strategy registry with all strategy configurations.
    
    Returns all registered strategies with their:
    - Preferred/anti regimes
    - Volatility preferences
    - Breadth requirements
    - Risk profiles
    """
    try:
        summary = get_registry_summary()
        
        # Add detailed configs
        configs = []
        for name, config in STRATEGY_REGISTRY.items():
            configs.append(config.to_dict())
        
        return {
            "status": "ok",
            "summary": summary,
            "configs": configs,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════
# STATE ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router.get("/state")
async def get_all_strategy_states(
    symbol: str = Query("BTC", description="Reference symbol for market context")
):
    """
    Get state for all strategies.
    
    Returns suitability and state for each strategy family
    based on current market conditions.
    """
    try:
        engine = get_strategy_state_engine()
        states = engine.compute_all_strategies(symbol)
        
        return {
            "status": "ok",
            "symbol": symbol,
            "strategy_count": len(states),
            "states": [s.to_dict() for s in states],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state/{strategy}")
async def get_strategy_state(
    strategy: str,
    symbol: str = Query("BTC", description="Reference symbol for market context")
):
    """
    Get state for a specific strategy.
    
    Returns detailed suitability breakdown for the strategy.
    """
    try:
        if strategy not in STRATEGY_REGISTRY:
            raise HTTPException(
                status_code=404, 
                detail=f"Strategy '{strategy}' not found. Available: {get_all_strategies()}"
            )
        
        engine = get_strategy_state_engine()
        state = engine.compute_strategy_state(strategy, symbol)
        
        return {
            "status": "ok",
            "symbol": symbol,
            "data": state.to_dict(),
            "market_context": state.market_context,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════
# SUMMARY ENDPOINT
# ══════════════════════════════════════════════════════════════

@router.get("/summary")
async def get_strategy_summary(
    symbol: str = Query("BTC", description="Reference symbol for market context")
):
    """
    Get aggregated strategy summary.
    
    Returns:
    - Market regime
    - Active strategies
    - Reduced strategies
    - Disabled strategies
    """
    try:
        engine = get_strategy_state_engine()
        summary = engine.compute_summary(symbol)
        
        return {
            "status": "ok",
            "symbol": symbol,
            "data": summary.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/full")
async def get_strategy_summary_full(
    symbol: str = Query("BTC", description="Reference symbol for market context")
):
    """
    Get full strategy summary with all details.
    
    Returns complete state for all strategies.
    """
    try:
        engine = get_strategy_state_engine()
        summary = engine.compute_summary(symbol)
        
        return {
            "status": "ok",
            "symbol": symbol,
            "data": summary.to_full_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════
# PHASE 19.2 — ALLOCATION ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router.get("/allocation")
async def get_all_allocations(
    symbol: str = Query("BTC", description="Reference symbol for market context")
):
    """
    Get capital allocation for all strategies.
    
    Returns allocation weights and capital shares
    based on strategy states.
    """
    try:
        engine = get_allocation_engine()
        allocations = engine.compute_all_allocations(symbol)
        
        return {
            "status": "ok",
            "symbol": symbol,
            "allocation_count": len(allocations),
            "allocations": [a.to_dict() for a in allocations],
            "base_weights": BASE_WEIGHTS,
            "state_multipliers": ALLOC_STATE_MULTIPLIERS,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/allocation/summary")
async def get_allocation_summary(
    symbol: str = Query("BTC", description="Reference symbol for market context")
):
    """
    Get aggregated allocation summary.
    
    Returns:
    - Total capital distribution
    - Active/Reduced/Disabled allocation
    - Per-strategy capital shares
    """
    try:
        engine = get_allocation_engine()
        summary = engine.compute_summary(symbol)
        
        return {
            "status": "ok",
            "symbol": symbol,
            "data": summary.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/allocation/summary/full")
async def get_allocation_summary_full(
    symbol: str = Query("BTC", description="Reference symbol for market context")
):
    """
    Get full allocation summary with all details.
    
    Returns complete allocation state for all strategies.
    """
    try:
        engine = get_allocation_engine()
        summary = engine.compute_summary(symbol)
        
        return {
            "status": "ok",
            "symbol": symbol,
            "data": summary.to_full_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/allocation/{strategy}")
async def get_strategy_allocation(
    strategy: str,
    symbol: str = Query("BTC", description="Reference symbol for market context")
):
    """
    Get allocation for a specific strategy.
    
    Returns detailed allocation breakdown for the strategy.
    """
    try:
        if strategy not in STRATEGY_REGISTRY:
            raise HTTPException(
                status_code=404, 
                detail=f"Strategy '{strategy}' not found. Available: {get_all_strategies()}"
            )
        
        engine = get_allocation_engine()
        alloc = engine.compute_allocation(strategy, symbol)
        
        return {
            "status": "ok",
            "symbol": symbol,
            "data": alloc.to_dict(),
            "base_weight": BASE_WEIGHTS.get(strategy, 0.0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ══════════════════════════════════════════════════════════════
# PHASE 19.3 — REGIME SWITCH ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router.get("/regime")
async def get_regime_map():
    """
    Get regime-strategy mapping configuration.
    
    Returns all defined regimes and their strategy priorities.
    """
    try:
        summary = get_regime_map_summary()
        
        return {
            "status": "ok",
            "data": summary,
            "priority_modifiers": PRIORITY_MODIFIERS,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regime/priority")
async def get_regime_priority(
    symbol: str = Query("BTC", description="Reference symbol for market context")
):
    """
    Get current strategy priorities based on regime.
    
    Returns:
    - Primary strategy
    - Secondary strategies
    - Inactive strategies
    - Modifiers per strategy
    """
    try:
        engine = get_regime_switch_engine()
        priority = engine.compute_regime_priority(symbol)
        
        return {
            "status": "ok",
            "symbol": symbol,
            "data": priority.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regime/summary")
async def get_regime_summary(
    symbols: str = Query("BTC,ETH,SOL", description="Comma-separated symbols")
):
    """
    Get regime summary across multiple symbols.
    
    Returns:
    - Dominant regime
    - Regime stability
    - Primary strategies
    """
    try:
        engine = get_regime_switch_engine()
        symbol_list = [s.strip() for s in symbols.split(",")]
        summary = engine.compute_summary(symbol_list)
        
        return {
            "status": "ok",
            "data": summary.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regime/{symbol}")
async def get_regime_for_symbol(symbol: str):
    """
    Get strategy priorities for a specific symbol.
    
    Returns detailed regime and priority information.
    """
    try:
        engine = get_regime_switch_engine()
        priority = engine.compute_regime_priority(symbol)
        
        return {
            "status": "ok",
            "symbol": symbol,
            "market_regime": priority.market_regime,
            "regime_confidence": round(priority.regime_confidence, 4),
            "primary_strategy": priority.primary_strategy,
            "secondary_strategies": priority.secondary_strategies,
            "inactive_strategies": priority.inactive_strategies,
            "strategy_modifiers": {
                k: {mk: round(mv, 4) for mk, mv in v.items()}
                for k, v in priority.strategy_modifiers.items()
            },
            "breakdown": {
                "regime_score": round(priority.regime_score, 4),
                "volatility_score": round(priority.volatility_score, 4),
                "breadth_score": round(priority.breadth_score, 4),
                "interaction_score": round(priority.interaction_score, 4),
                "ecology_score": round(priority.ecology_score, 4),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ══════════════════════════════════════════════════════════════
# PHASE 19.4 — AGGREGATOR ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router.get("/aggregate")
async def get_aggregate(
    symbol: str = Query("BTC", description="Reference symbol for market context")
):
    """
    Get aggregated Strategy Brain state.
    
    Combines:
    - Strategy state (active/reduced/disabled)
    - Allocation (capital shares)
    - Regime priority (primary/secondary)
    
    Returns unified overlay for Trading Product.
    """
    try:
        aggregator = get_strategy_brain_aggregator()
        state = aggregator.compute_aggregate(symbol)
        
        return {
            "status": "ok",
            "symbol": symbol,
            "data": state.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aggregate/summary")
async def get_aggregate_summary(
    symbol: str = Query("BTC", description="Reference symbol for market context")
):
    """
    Get compact Strategy Brain summary.
    
    Returns minimal overlay data for quick integration.
    """
    try:
        aggregator = get_strategy_brain_aggregator()
        state = aggregator.compute_aggregate(symbol)
        
        return {
            "status": "ok",
            "symbol": symbol,
            "data": state.to_summary(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aggregate/trading-product")
async def get_aggregate_trading_product(
    symbol: str = Query("BTC", description="Reference symbol for market context")
):
    """
    Get Strategy Brain overlay for Trading Product.
    
    Returns block formatted for Trading Product snapshot integration.
    """
    try:
        aggregator = get_strategy_brain_aggregator()
        overlay = aggregator.get_trading_product_overlay(symbol)
        
        return {
            "status": "ok",
            "symbol": symbol,
            "data": overlay,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════
# PHASE 24.3 — FRACTAL HINT ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router.get("/fractal-hint/{symbol}")
async def get_fractal_hint(symbol: str):
    """
    PHASE 24.3: Get fractal hint for Strategy Brain.
    
    Returns fractal phase and how it affects strategy suitability.
    
    Key principle: Fractal influence is LIMITED to ≤10% of regime score.
    """
    try:
        from modules.strategy_brain.fractal_hint import get_fractal_hint_engine
        
        engine = get_fractal_hint_engine()
        hint = engine.get_fractal_hint(symbol.upper())
        strategy_hints = engine.compute_all_strategy_hints(hint)
        regime_hint = engine.get_regime_hint(symbol.upper())
        
        return {
            "status": "ok",
            "symbol": symbol.upper(),
            "fractal_hint": hint.to_dict(),
            "regime_hint": regime_hint,
            "strategy_hints": {
                k: v.to_dict() for k, v in strategy_hints.items()
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fractal-hint/summary/{symbol}")
async def get_fractal_hint_summary(symbol: str):
    """
    PHASE 24.3: Quick fractal hint summary.
    """
    try:
        from modules.strategy_brain.fractal_hint import get_fractal_hint_engine
        
        engine = get_fractal_hint_engine()
        hint = engine.get_fractal_hint(symbol.upper())
        
        return {
            "status": "ok",
            "symbol": symbol.upper(),
            "phase": hint.phase.value,
            "phase_confidence": round(hint.phase_confidence, 4),
            "fractal_strength": round(hint.fractal_strength, 4),
            "context_state": hint.context_state,
            "is_active": hint.is_active(),
            "supported_strategies": hint.get_supported_strategies(),
            "anti_strategies": hint.get_anti_strategies(),
            "regime_hint": hint.get_regime_hint(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

