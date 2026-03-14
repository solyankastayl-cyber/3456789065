"""
PHASE 19.1 — Strategy Brain Types
=================================
Type definitions for Strategy Brain module.

Core contracts:
- StrategyType: Enum of strategy families
- StrategyState: State output for a strategy
- StrategySummary: Aggregated summary
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone


# ══════════════════════════════════════════════════════════════
# STRATEGY TYPE ENUM
# ══════════════════════════════════════════════════════════════

class StrategyType(str, Enum):
    """Strategy family types."""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    LIQUIDATION_CAPTURE = "liquidation_capture"
    FLOW_FOLLOWING = "flow_following"
    VOLATILITY_EXPANSION = "volatility_expansion"
    FUNDING_ARB = "funding_arb"
    STRUCTURE_REVERSAL = "structure_reversal"


class StrategyStateEnum(str, Enum):
    """Strategy state enum."""
    ACTIVE = "ACTIVE"        # Full operation
    REDUCED = "REDUCED"      # Reduced allocation
    DISABLED = "DISABLED"    # No new positions


class RiskProfile(str, Enum):
    """Risk profile for strategies."""
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"


# ══════════════════════════════════════════════════════════════
# REGIME TYPES (from existing modules)
# ══════════════════════════════════════════════════════════════

class TrendState(str, Enum):
    """Trend states from MarketState."""
    TREND_UP = "TREND_UP"
    TREND_DOWN = "TREND_DOWN"
    RANGE = "RANGE"
    MIXED = "MIXED"


class VolatilityState(str, Enum):
    """Volatility states from MarketState."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    EXPANDING = "EXPANDING"
    CONTRACTING = "CONTRACTING"


class BreadthState(str, Enum):
    """Breadth states from MarketStructure."""
    STRONG = "STRONG"
    MIXED = "MIXED"
    WEAK = "WEAK"


class InteractionState(str, Enum):
    """Interaction states from AlphaInteraction."""
    REINFORCED = "REINFORCED"
    NEUTRAL = "NEUTRAL"
    CONFLICTED = "CONFLICTED"
    CANCELLED = "CANCELLED"


# ══════════════════════════════════════════════════════════════
# STRATEGY CONFIG
# ══════════════════════════════════════════════════════════════

@dataclass
class StrategyConfig:
    """Configuration for a strategy family."""
    strategy_type: StrategyType
    name: str
    description: str
    
    # Regime suitability
    preferred_regimes: List[str]      # Regimes where strategy works best
    anti_regimes: List[str]           # Regimes where strategy fails
    
    # Volatility preferences
    preferred_volatility: List[str]   # LOW, NORMAL, HIGH, EXPANDING, CONTRACTING
    anti_volatility: List[str]
    
    # Breadth requirements
    min_breadth: str                  # Minimum breadth state required
    
    # Interaction requirements
    preferred_interaction: List[str]  # REINFORCED, NEUTRAL, etc.
    anti_interaction: List[str]
    
    # Risk profile
    risk_profile: RiskProfile
    
    # Default state
    default_state: StrategyStateEnum
    
    # Base weights for suitability calculation
    regime_weight: float = 0.35
    volatility_weight: float = 0.20
    breadth_weight: float = 0.20
    interaction_weight: float = 0.15
    ecology_weight: float = 0.10
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "strategy_type": self.strategy_type.value,
            "name": self.name,
            "description": self.description,
            "preferred_regimes": self.preferred_regimes,
            "anti_regimes": self.anti_regimes,
            "preferred_volatility": self.preferred_volatility,
            "anti_volatility": self.anti_volatility,
            "min_breadth": self.min_breadth,
            "preferred_interaction": self.preferred_interaction,
            "anti_interaction": self.anti_interaction,
            "risk_profile": self.risk_profile.value,
            "default_state": self.default_state.value,
        }


# ══════════════════════════════════════════════════════════════
# STRATEGY STATE OUTPUT
# ══════════════════════════════════════════════════════════════

@dataclass
class StrategyState:
    """
    State output for a single strategy.
    
    This is the core output contract for Strategy Brain.
    """
    strategy_name: str
    strategy_type: StrategyType
    strategy_state: StrategyStateEnum
    suitability_score: float          # 0.0 - 1.0
    confidence_modifier: float        # Applied to signal confidence
    capital_modifier: float           # Applied to position size
    reason: str
    timestamp: datetime
    
    # Breakdown scores
    regime_score: float = 0.0
    volatility_score: float = 0.0
    breadth_score: float = 0.0
    interaction_score: float = 0.0
    ecology_score: float = 0.0
    
    # Input context
    market_context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "strategy_name": self.strategy_name,
            "strategy_type": self.strategy_type.value,
            "strategy_state": self.strategy_state.value,
            "suitability_score": round(self.suitability_score, 4),
            "confidence_modifier": round(self.confidence_modifier, 4),
            "capital_modifier": round(self.capital_modifier, 4),
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "breakdown": {
                "regime_score": round(self.regime_score, 4),
                "volatility_score": round(self.volatility_score, 4),
                "breadth_score": round(self.breadth_score, 4),
                "interaction_score": round(self.interaction_score, 4),
                "ecology_score": round(self.ecology_score, 4),
            },
        }
    
    def to_summary(self) -> Dict[str, Any]:
        """Compact summary."""
        return {
            "name": self.strategy_name,
            "state": self.strategy_state.value,
            "score": round(self.suitability_score, 3),
            "conf_mod": round(self.confidence_modifier, 3),
            "cap_mod": round(self.capital_modifier, 3),
        }


# ══════════════════════════════════════════════════════════════
# STRATEGY SUMMARY
# ══════════════════════════════════════════════════════════════

@dataclass
class StrategySummary:
    """
    Aggregated summary of all strategy states.
    
    Global view of which strategies are suitable.
    """
    market_regime: str
    volatility_state: str
    breadth_state: str
    interaction_state: str
    ecology_state: str
    
    active_strategies: List[str]
    reduced_strategies: List[str]
    disabled_strategies: List[str]
    
    strategy_count: int
    active_count: int
    reduced_count: int
    disabled_count: int
    
    timestamp: datetime
    
    # Full states
    strategy_states: List[StrategyState] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "market_regime": self.market_regime,
            "volatility_state": self.volatility_state,
            "breadth_state": self.breadth_state,
            "interaction_state": self.interaction_state,
            "ecology_state": self.ecology_state,
            "active_strategies": self.active_strategies,
            "reduced_strategies": self.reduced_strategies,
            "disabled_strategies": self.disabled_strategies,
            "counts": {
                "total": self.strategy_count,
                "active": self.active_count,
                "reduced": self.reduced_count,
                "disabled": self.disabled_count,
            },
            "timestamp": self.timestamp.isoformat(),
        }
    
    def to_full_dict(self) -> Dict[str, Any]:
        """Full dictionary with all strategy details."""
        result = self.to_dict()
        result["strategies"] = [s.to_dict() for s in self.strategy_states]
        return result


# ══════════════════════════════════════════════════════════════
# STATE THRESHOLDS
# ══════════════════════════════════════════════════════════════

STATE_THRESHOLDS = {
    "ACTIVE": 0.70,      # suitability >= 0.70
    "REDUCED": 0.45,     # suitability >= 0.45
    "DISABLED": 0.0,     # suitability < 0.45
}

STATE_MODIFIERS = {
    StrategyStateEnum.ACTIVE: {
        "confidence_modifier": 1.05,
        "capital_modifier": 1.10,
    },
    StrategyStateEnum.REDUCED: {
        "confidence_modifier": 0.90,
        "capital_modifier": 0.80,
    },
    StrategyStateEnum.DISABLED: {
        "confidence_modifier": 0.70,
        "capital_modifier": 0.00,
    },
}
