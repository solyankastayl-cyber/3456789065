"""
PHASE 19.1 — Strategy Brain Module
==================================
Strategy-level management layer.

Manages which strategies should be:
- ACTIVE
- REDUCED  
- DISABLED

Based on market conditions, regime, ecology, and interactions.
"""

from modules.strategy_brain.strategy_types import (
    StrategyType,
    StrategyState,
    StrategyStateEnum,
    RiskProfile,
)
from modules.strategy_brain.strategy_registry import (
    STRATEGY_REGISTRY,
    get_strategy_config,
)
from modules.strategy_brain.strategy_state_engine import (
    get_strategy_state_engine,
)

__all__ = [
    "StrategyType",
    "StrategyState", 
    "StrategyStateEnum",
    "RiskProfile",
    "STRATEGY_REGISTRY",
    "get_strategy_config",
    "get_strategy_state_engine",
]
