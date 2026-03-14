"""
Hypothesis Scoring Engine

PHASE 29.2 — Hypothesis Scoring Engine

Separates hypothesis evaluation into 3 independent components:

1. structural_score — How market-logically sound is the idea
2. execution_score — How safe is it to trade now
3. conflict_score — How much do layers contradict each other

Confidence and reliability are then computed from these scores.

Key principles:
- Idea strength (structural) is separate from execution quality
- This separates quant research layer from simple signal generator
"""

import math
from typing import Optional, Dict, Literal
from datetime import datetime

from .hypothesis_types import (
    MarketHypothesis,
    HypothesisCandidate,
    HypothesisInputLayers,
)


# ══════════════════════════════════════════════════════════════
# Constants — Structural Score Weights
# ══════════════════════════════════════════════════════════════

STRUCTURAL_WEIGHT_ALPHA = 0.40
STRUCTURAL_WEIGHT_REGIME = 0.30
STRUCTURAL_WEIGHT_MACRO = 0.20
STRUCTURAL_WEIGHT_ALIGNMENT = 0.10

# ══════════════════════════════════════════════════════════════
# Constants — Execution Score Weights
# ══════════════════════════════════════════════════════════════

EXECUTION_WEIGHT_MICROSTRUCTURE = 0.50
EXECUTION_WEIGHT_CONTEXT = 0.30
EXECUTION_WEIGHT_REGIME_STABILITY = 0.20

# ══════════════════════════════════════════════════════════════
# Constants — Confidence/Reliability Weights
# ══════════════════════════════════════════════════════════════

CONFIDENCE_STRUCTURAL_WEIGHT = 0.60
CONFIDENCE_EXECUTION_WEIGHT = 0.40

# ══════════════════════════════════════════════════════════════
# Constants — Microstructure Quality Mapping
# ══════════════════════════════════════════════════════════════

MICROSTRUCTURE_QUALITY_MAP = {
    "SUPPORTIVE": 1.0,
    "NEUTRAL": 0.7,
    "FRAGILE": 0.45,
    "STRESSED": 0.25,
}

# ══════════════════════════════════════════════════════════════
# Constants — Regime Stability Mapping
# ══════════════════════════════════════════════════════════════

REGIME_STABILITY_MAP = {
    "STABLE": 1.0,
    "EARLY_SHIFT": 0.7,
    "ACTIVE_TRANSITION": 0.5,
    "UNSTABLE": 0.3,
}

# ══════════════════════════════════════════════════════════════
# Constants — Execution State Thresholds
# ══════════════════════════════════════════════════════════════

EXECUTION_STATE_FAVORABLE_THRESHOLD = 0.70
EXECUTION_STATE_CAUTIOUS_THRESHOLD = 0.45

# ══════════════════════════════════════════════════════════════
# Constants — Conflict Interpretation
# ══════════════════════════════════════════════════════════════

CONFLICT_LOW_THRESHOLD = 0.10
CONFLICT_HIGH_THRESHOLD = 0.25

ConflictLevel = Literal["LOW_CONFLICT", "MODERATE", "HIGH"]


# ══════════════════════════════════════════════════════════════
# Extended Input Layers (with execution context)
# ══════════════════════════════════════════════════════════════

class HypothesisScoringInput:
    """
    Extended input for hypothesis scoring.
    
    Adds execution context and regime transition data.
    """
    
    def __init__(
        self,
        # From HypothesisInputLayers
        layers: HypothesisInputLayers,
        # Execution context
        execution_confidence_modifier: float = 1.0,
        # Regime transition
        transition_state: str = "STABLE",
    ):
        self.layers = layers
        self.execution_confidence_modifier = execution_confidence_modifier
        self.transition_state = transition_state


# ══════════════════════════════════════════════════════════════
# Hypothesis Scoring Engine
# ══════════════════════════════════════════════════════════════

class HypothesisScoringEngine:
    """
    Hypothesis Scoring Engine — PHASE 29.2
    
    Computes:
    - structural_score: idea quality
    - execution_score: execution safety
    - conflict_score: layer disagreement
    - confidence: combined score
    - reliability: stability of hypothesis
    """
    
    def __init__(self):
        pass
    
    # ═══════════════════════════════════════════════════════════
    # 1. Hypothesis Alignment
    # ═══════════════════════════════════════════════════════════
    
    def calculate_hypothesis_alignment(
        self,
        hypothesis_type: str,
        regime_type: str,
        directional_bias: str,
    ) -> float:
        """
        Calculate alignment score based on hypothesis type.
        
        BULLISH_CONTINUATION:
            regime = TRENDING + bias = LONG → 1.0
            regime ≠ TRENDING → 0.6
        
        BEARISH_CONTINUATION:
            regime = TRENDING + bias = SHORT → 1.0
            regime ≠ TRENDING → 0.6
        
        RANGE_MEAN_REVERSION:
            regime = RANGING → 1.0
            else → 0.5
        
        BREAKOUT_FORMING:
            regime in (TRENDING, transition) → 0.9
            else → 0.6
        
        NO_EDGE:
            always → 0.3
        """
        if hypothesis_type == "BULLISH_CONTINUATION":
            if regime_type == "TRENDING" and directional_bias == "LONG":
                return 1.0
            elif regime_type == "TRENDING":
                return 0.8
            else:
                return 0.6
        
        elif hypothesis_type == "BEARISH_CONTINUATION":
            if regime_type == "TRENDING" and directional_bias == "SHORT":
                return 1.0
            elif regime_type == "TRENDING":
                return 0.8
            else:
                return 0.6
        
        elif hypothesis_type == "RANGE_MEAN_REVERSION":
            if regime_type == "RANGING":
                return 1.0
            else:
                return 0.5
        
        elif hypothesis_type == "BREAKOUT_FORMING":
            if regime_type in ("TRENDING", "VOLATILE"):
                return 0.9
            else:
                return 0.6
        
        elif hypothesis_type == "NO_EDGE":
            return 0.3
        
        # Default for unknown types
        return 0.5
    
    # ═══════════════════════════════════════════════════════════
    # 2. Structural Score
    # ═══════════════════════════════════════════════════════════
    
    def calculate_structural_score(
        self,
        candidate: HypothesisCandidate,
        layers: HypothesisInputLayers,
    ) -> float:
        """
        Calculate structural score.
        
        Formula:
        structural_score =
            0.40 * alpha_support
            + 0.30 * regime_support
            + 0.20 * macro_fractal_support
            + 0.10 * hypothesis_alignment
        """
        # Get hypothesis alignment
        alignment = self.calculate_hypothesis_alignment(
            hypothesis_type=candidate.hypothesis_type,
            regime_type=layers.regime_type,
            directional_bias=candidate.directional_bias,
        )
        
        score = (
            STRUCTURAL_WEIGHT_ALPHA * candidate.alpha_support
            + STRUCTURAL_WEIGHT_REGIME * candidate.regime_support
            + STRUCTURAL_WEIGHT_MACRO * candidate.macro_support
            + STRUCTURAL_WEIGHT_ALIGNMENT * alignment
        )
        
        return round(min(max(score, 0.0), 1.0), 4)
    
    # ═══════════════════════════════════════════════════════════
    # 3. Execution Score
    # ═══════════════════════════════════════════════════════════
    
    def calculate_microstructure_execution_quality(
        self,
        microstructure_state: str,
    ) -> float:
        """
        Map microstructure state to execution quality.
        
        SUPPORTIVE → 1.0
        NEUTRAL → 0.7
        FRAGILE → 0.45
        STRESSED → 0.25
        """
        return MICROSTRUCTURE_QUALITY_MAP.get(microstructure_state, 0.5)
    
    def calculate_execution_context_modifier(
        self,
        confidence_modifier: float,
    ) -> float:
        """
        Normalize execution context confidence_modifier to [0, 1].
        
        MicrostructureContext.confidence_modifier range: [0.82, 1.12]
        
        Formula:
        normalized = (modifier - 0.82) / (1.12 - 0.82)
        """
        min_mod = 0.82
        max_mod = 1.12
        
        normalized = (confidence_modifier - min_mod) / (max_mod - min_mod)
        return round(min(max(normalized, 0.0), 1.0), 4)
    
    def calculate_regime_stability(
        self,
        transition_state: str,
    ) -> float:
        """
        Map regime transition state to stability score.
        
        STABLE → 1.0
        EARLY_SHIFT → 0.7
        ACTIVE_TRANSITION → 0.5
        UNSTABLE → 0.3
        """
        return REGIME_STABILITY_MAP.get(transition_state, 0.7)
    
    def calculate_execution_score(
        self,
        microstructure_state: str,
        confidence_modifier: float,
        transition_state: str,
    ) -> float:
        """
        Calculate execution score.
        
        Formula:
        execution_score =
            0.50 * microstructure_execution_quality
            + 0.30 * execution_context_modifier
            + 0.20 * regime_stability
        """
        micro_quality = self.calculate_microstructure_execution_quality(
            microstructure_state
        )
        exec_modifier = self.calculate_execution_context_modifier(
            confidence_modifier
        )
        regime_stability = self.calculate_regime_stability(
            transition_state
        )
        
        score = (
            EXECUTION_WEIGHT_MICROSTRUCTURE * micro_quality
            + EXECUTION_WEIGHT_CONTEXT * exec_modifier
            + EXECUTION_WEIGHT_REGIME_STABILITY * regime_stability
        )
        
        return round(min(max(score, 0.0), 1.0), 4)
    
    # ═══════════════════════════════════════════════════════════
    # 4. Conflict Score
    # ═══════════════════════════════════════════════════════════
    
    def calculate_conflict_score(
        self,
        alpha_support: float,
        regime_support: float,
        microstructure_support: float,
    ) -> float:
        """
        Calculate conflict score as standard deviation of support values.
        
        Formula:
        conflict_score = std(alpha_support, regime_support, microstructure_support)
        
        Normalized to [0, 1].
        
        Interpretation:
        < 0.10 → LOW_CONFLICT
        0.10 - 0.25 → MODERATE
        > 0.25 → HIGH
        """
        values = [alpha_support, regime_support, microstructure_support]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = math.sqrt(variance)
        
        # Normalize: max std for 3 values in [0,1] is ~0.47
        # But for practical interpretation, we keep raw std
        return round(min(max(std, 0.0), 1.0), 4)
    
    def interpret_conflict_level(
        self,
        conflict_score: float,
    ) -> ConflictLevel:
        """
        Interpret conflict score.
        
        < 0.10 → LOW_CONFLICT
        0.10 - 0.25 → MODERATE
        > 0.25 → HIGH
        """
        if conflict_score < CONFLICT_LOW_THRESHOLD:
            return "LOW_CONFLICT"
        elif conflict_score <= CONFLICT_HIGH_THRESHOLD:
            return "MODERATE"
        else:
            return "HIGH"
    
    # ═══════════════════════════════════════════════════════════
    # 5. Confidence
    # ═══════════════════════════════════════════════════════════
    
    def calculate_confidence(
        self,
        structural_score: float,
        execution_score: float,
    ) -> float:
        """
        Calculate confidence as weighted combination.
        
        Formula:
        confidence = 0.60 * structural_score + 0.40 * execution_score
        """
        confidence = (
            CONFIDENCE_STRUCTURAL_WEIGHT * structural_score
            + CONFIDENCE_EXECUTION_WEIGHT * execution_score
        )
        return round(min(max(confidence, 0.0), 1.0), 4)
    
    # ═══════════════════════════════════════════════════════════
    # 6. Reliability
    # ═══════════════════════════════════════════════════════════
    
    def calculate_reliability(
        self,
        conflict_score: float,
        regime_support: float,
    ) -> float:
        """
        Calculate reliability showing hypothesis stability.
        
        Formula:
        reliability = (1 - conflict_score) * regime_support
        
        Clipped to [0, 1].
        """
        reliability = (1.0 - conflict_score) * regime_support
        return round(min(max(reliability, 0.0), 1.0), 4)
    
    # ═══════════════════════════════════════════════════════════
    # 7. Execution State
    # ═══════════════════════════════════════════════════════════
    
    def map_execution_state(
        self,
        execution_score: float,
    ) -> str:
        """
        Map execution score to execution state.
        
        execution_score >= 0.70 → FAVORABLE
        0.45 <= score < 0.70 → CAUTIOUS
        score < 0.45 → UNFAVORABLE
        """
        if execution_score >= EXECUTION_STATE_FAVORABLE_THRESHOLD:
            return "FAVORABLE"
        elif execution_score >= EXECUTION_STATE_CAUTIOUS_THRESHOLD:
            return "CAUTIOUS"
        else:
            return "UNFAVORABLE"
    
    # ═══════════════════════════════════════════════════════════
    # 8. Full Scoring
    # ═══════════════════════════════════════════════════════════
    
    def score_hypothesis(
        self,
        candidate: HypothesisCandidate,
        layers: HypothesisInputLayers,
        execution_confidence_modifier: float = 1.0,
        transition_state: str = "STABLE",
    ) -> Dict:
        """
        Full hypothesis scoring.
        
        Returns all scores and derived values.
        """
        # 1. Structural score
        structural_score = self.calculate_structural_score(candidate, layers)
        
        # 2. Execution score
        execution_score = self.calculate_execution_score(
            microstructure_state=layers.microstructure_state,
            confidence_modifier=execution_confidence_modifier,
            transition_state=transition_state,
        )
        
        # 3. Conflict score
        conflict_score = self.calculate_conflict_score(
            alpha_support=candidate.alpha_support,
            regime_support=candidate.regime_support,
            microstructure_support=candidate.microstructure_support,
        )
        
        # 4. Confidence
        confidence = self.calculate_confidence(structural_score, execution_score)
        
        # 5. Reliability
        reliability = self.calculate_reliability(conflict_score, candidate.regime_support)
        
        # 6. Execution state
        execution_state = self.map_execution_state(execution_score)
        
        # 7. Conflict level
        conflict_level = self.interpret_conflict_level(conflict_score)
        
        return {
            "structural_score": structural_score,
            "execution_score": execution_score,
            "conflict_score": conflict_score,
            "confidence": confidence,
            "reliability": reliability,
            "execution_state": execution_state,
            "conflict_level": conflict_level,
            "hypothesis_alignment": self.calculate_hypothesis_alignment(
                candidate.hypothesis_type,
                layers.regime_type,
                candidate.directional_bias,
            ),
        }
    
    # ═══════════════════════════════════════════════════════════
    # 9. Enhanced Reason Generation
    # ═══════════════════════════════════════════════════════════
    
    def generate_enhanced_reason(
        self,
        hypothesis_type: str,
        scores: Dict,
        layers: HypothesisInputLayers,
    ) -> str:
        """
        Generate enhanced reason explaining hypothesis scores.
        """
        parts = []
        
        # Base hypothesis description
        type_descriptions = {
            "BULLISH_CONTINUATION": "bullish continuation structure",
            "BEARISH_CONTINUATION": "bearish continuation structure",
            "BREAKOUT_FORMING": "breakout formation",
            "RANGE_MEAN_REVERSION": "range mean reversion setup",
            "NO_EDGE": "no clear edge",
        }
        
        parts.append(type_descriptions.get(
            hypothesis_type,
            hypothesis_type.lower().replace("_", " ")
        ))
        
        # Add support factors
        support_factors = []
        if scores["structural_score"] >= 0.6:
            support_factors.append("strong structural alignment")
        if layers.regime_confidence >= 0.6:
            support_factors.append("regime confirmation")
        if layers.alpha_strength >= 0.6:
            support_factors.append("alpha factor support")
        
        if support_factors:
            parts.append("supported by " + " and ".join(support_factors))
        
        # Add execution quality note
        if scores["execution_score"] < 0.45:
            parts.append("but execution quality reduced by")
            if layers.microstructure_state in ("FRAGILE", "STRESSED"):
                parts.append(f"{layers.microstructure_state.lower()} microstructure")
            else:
                parts.append("unfavorable conditions")
        elif scores["execution_score"] >= 0.70:
            parts.append("with favorable execution conditions")
        
        # Add conflict note if high
        if scores["conflict_level"] == "HIGH":
            parts.append("(high layer conflict detected)")
        
        return " ".join(parts)


# ══════════════════════════════════════════════════════════════
# Singleton
# ══════════════════════════════════════════════════════════════

_scoring_engine: Optional[HypothesisScoringEngine] = None


def get_hypothesis_scoring_engine() -> HypothesisScoringEngine:
    """Get singleton instance of HypothesisScoringEngine."""
    global _scoring_engine
    if _scoring_engine is None:
        _scoring_engine = HypothesisScoringEngine()
    return _scoring_engine
