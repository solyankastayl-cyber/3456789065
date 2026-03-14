# Hypothesis Engine — Architecture Documentation

## PHASE 29 — HYPOTHESIS ENGINE V1 FROZEN

**Status:** PRODUCTION-READY  
**Version:** 1.0.0  
**Freeze Date:** 2026-03-14

---

## Overview

Hypothesis Engine is the **market interpretation layer** that sits between Intelligence Layers and Strategy Brain.

```
Market Data
    ↓
TA / Exchange Intelligence
    ↓
┌─────────────────────────────────────┐
│        Intelligence Layers          │
├─────────────────────────────────────┤
│  • Macro-Fractal Layer              │
│  • Alpha Factory                    │
│  • Regime Intelligence              │
│  • Microstructure Intelligence      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│      HYPOTHESIS ENGINE (Frozen)     │
├─────────────────────────────────────┤
│  29.1 Core Engine                   │
│  29.2 Scoring Engine                │
│  29.3 Conflict Resolver             │
│  29.4 Registry / History            │
│  29.5 Strategy Integration          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│          Strategy Brain             │
└─────────────────────────────────────┘
    ↓
Strategy Execution
```

---

## Architecture Rules (FROZEN)

### Rule 1: NO Order Placement
Hypothesis Engine **DOES NOT** place orders.

### Rule 2: NO Final Execution
Hypothesis Engine **DOES NOT** do final execution.

### Rule 3: NO Alpha Factory Replacement
Hypothesis Engine **DOES NOT** replace Alpha Factory.  
It consumes Alpha Factory signals.

### Rule 4: NO Regime Intelligence Replacement
Hypothesis Engine **DOES NOT** replace Regime Intelligence.  
It consumes Regime Intelligence context.

### Rule 5: Market Interpretation Only
Hypothesis Engine **INTERPRETS** market state and passes result to Strategy Brain.

---

## Module Structure (FROZEN)

```
/modules/hypothesis_engine/
├── __init__.py
├── hypothesis_types.py           # Contracts
├── hypothesis_engine.py          # Core Engine (29.1)
├── hypothesis_scoring_engine.py  # Scoring Engine (29.2)
├── hypothesis_conflict_resolver.py # Conflict Resolver (29.3)
├── hypothesis_registry.py        # Registry / History (29.4)
├── hypothesis_routes.py          # API Routes
└── tests/
    ├── hypothesis_scoring_tests.py
    ├── hypothesis_conflict_resolver_tests.py
    └── hypothesis_registry_tests.py

/modules/strategy_brain/          # Strategy Integration (29.5)
├── __init__.py
├── strategy_types.py
├── strategy_brain_engine.py
├── strategy_routes.py
└── strategy_tests.py
```

---

## Frozen Contract: MarketHypothesis

```json
{
  "symbol": "BTC",
  "hypothesis_type": "BREAKOUT_FORMING",
  "directional_bias": "LONG",

  "structural_score": 0.71,
  "execution_score": 0.58,
  "conflict_score": 0.12,
  "conflict_state": "MODERATE_CONFLICT",

  "confidence": 0.65,
  "reliability": 0.56,

  "alpha_support": 0.70,
  "regime_support": 0.65,
  "microstructure_support": 0.60,
  "macro_fractal_support": 0.55,

  "execution_state": "CAUTIOUS",

  "reason": "breakout structure supported by alpha and regime alignment but execution quality reduced by fragile liquidity",
  
  "created_at": "2026-03-14T12:00:00Z"
}
```

---

## Hypothesis Types (FROZEN)

| Type | Description | Strategy Mapping |
|------|-------------|------------------|
| BULLISH_CONTINUATION | Upward trend continuation | trend_following, breakout_trading |
| BEARISH_CONTINUATION | Downward trend continuation | trend_following, volatility_expansion |
| BREAKOUT_FORMING | Breakout setup forming | breakout_trading, volatility_expansion |
| RANGE_MEAN_REVERSION | Range-bound mean reversion | mean_reversion, range_trading |
| SHORT_SQUEEZE_SETUP | Short squeeze potential | liquidation_capture, volatility_expansion |
| LONG_SQUEEZE_SETUP | Long squeeze potential | liquidation_capture, volatility_expansion |
| VOLATILE_UNWIND | Volatility unwinding | volatility_expansion, mean_reversion |
| BREAKOUT_FAILURE_RISK | Breakout failure risk | mean_reversion, range_trading |
| NO_EDGE | No clear edge | none (blocked) |

---

## Scoring Formulas (FROZEN)

### Structural Score (29.2)

```
structural_score = 
    0.40 × alpha_support
  + 0.30 × regime_support
  + 0.20 × macro_fractal_support
  + 0.10 × hypothesis_alignment
```

### Execution Score (29.2)

```
execution_score = 
    0.50 × microstructure_execution_quality
  + 0.30 × execution_context_modifier
  + 0.20 × regime_stability
```

### Conflict Score (29.2)

```
conflict_score = std(alpha_support, regime_support, microstructure_support)
```

### Confidence (29.2)

```
confidence = 0.60 × structural_score + 0.40 × execution_score
```

### Reliability (29.2)

```
reliability = (1 - conflict_score) × regime_support
```

### Suitability Score (29.5)

```
suitability_score = 
    0.45 × confidence
  + 0.25 × reliability
  + 0.20 × regime_support
  + 0.10 × microstructure_quality
```

---

## Conflict Thresholds (FROZEN)

| Conflict Score | State | Confidence Modifier | Reliability Modifier | Execution State |
|----------------|-------|---------------------|----------------------|-----------------|
| < 0.10 | LOW_CONFLICT | 1.00 | 1.00 | No change |
| 0.10 - 0.25 | MODERATE_CONFLICT | 0.90 | 0.90 | FAVORABLE → CAUTIOUS |
| ≥ 0.25 | HIGH_CONFLICT | 0.70 | 0.75 | → UNFAVORABLE |

---

## Execution State Thresholds (FROZEN)

| Execution Score | State |
|-----------------|-------|
| ≥ 0.70 | FAVORABLE |
| 0.45 - 0.70 | CAUTIOUS |
| < 0.45 | UNFAVORABLE |

---

## Microstructure Quality Mapping (FROZEN)

| State | Quality |
|-------|---------|
| SUPPORTIVE | 1.0 |
| NEUTRAL | 0.7 |
| FRAGILE | 0.45 |
| STRESSED | 0.25 |

---

## Dependencies (FROZEN)

### Allowed Dependencies

✅ Alpha Factory  
✅ Regime Intelligence  
✅ Microstructure Intelligence  
✅ Macro-Fractal Context  
✅ Execution Context  
✅ Market Data

### Forbidden Dependencies

❌ Order Placement  
❌ Portfolio Execution  
❌ Risk Order Routing  
❌ Trade Management  
❌ Position Sizing (direct)

---

## API Endpoints (FROZEN)

### Hypothesis Engine

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/hypothesis/current/{symbol} | Current hypothesis |
| GET | /api/v1/hypothesis/history/{symbol} | Hypothesis history |
| GET | /api/v1/hypothesis/summary/{symbol} | Summary statistics |
| GET | /api/v1/hypothesis/stats/{symbol} | Full statistics |
| GET | /api/v1/hypothesis/recent | Recent (all symbols) |
| GET | /api/v1/hypothesis/symbols | Tracked symbols |
| POST | /api/v1/hypothesis/recompute/{symbol} | Force recompute |

### Strategy Brain

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/strategy/decision/{symbol} | Strategy decision |
| GET | /api/v1/strategy/summary/{symbol} | Strategy statistics |
| GET | /api/v1/strategy/history/{symbol} | Decision history |
| GET | /api/v1/strategy/available | Available strategies |
| POST | /api/v1/strategy/recompute/{symbol} | Force recompute |

---

## Integration Points (FROZEN)

### Input: Intelligence Layers

```python
HypothesisInputLayers:
  - alpha_direction: str
  - alpha_strength: float
  - alpha_breakout_strength: float
  - alpha_mean_reversion_strength: float
  - regime_type: str
  - regime_confidence: float
  - regime_in_transition: bool
  - microstructure_state: str
  - microstructure_confidence: float
  - vacuum_direction: str
  - pressure_directional: bool
  - pressure_direction: str
  - macro_confidence: float
```

### Output: Strategy Brain

```python
StrategyDecision:
  - symbol: str
  - hypothesis_type: str
  - directional_bias: str
  - selected_strategy: str
  - alternative_strategies: List[str]
  - suitability_score: float
  - execution_state: str
  - confidence: float
  - reliability: float
  - reason: str
```

---

## Test Coverage (FROZEN)

| Phase | Module | Tests |
|-------|--------|-------|
| 29.1 | Core Engine | 25 |
| 29.2 | Scoring Engine | 25 |
| 29.3 | Conflict Resolver | 20 |
| 29.4 | Registry / History | 22 |
| 29.5 | Strategy Brain | 24 |
| **Total** | | **116 tests** |

---

## Version History

| Version | Date | Phase | Description |
|---------|------|-------|-------------|
| 0.1.0 | 2026-03-14 | 29.1 | Core Engine + Contract |
| 0.2.0 | 2026-03-14 | 29.2 | Scoring Engine |
| 0.3.0 | 2026-03-14 | 29.3 | Conflict Resolver |
| 0.4.0 | 2026-03-14 | 29.4 | Registry / History |
| 0.5.0 | 2026-03-14 | 29.5 | Strategy Integration |
| **1.0.0** | **2026-03-14** | **29.6** | **FROZEN** |

---

## Future Extensions (Outside Frozen Layer)

The following extensions are **NOT** part of the frozen Hypothesis Engine:

- Hypothesis Competition Model (PHASE 30+)
- Hypothesis Outcome Engine
- Capital Allocation Integration
- Real-time WebSocket Streaming

These will be implemented as **separate layers** on top of the frozen engine.

---

## Freeze Certification

```
HYPOTHESIS ENGINE V1
Status: FROZEN
Date: 2026-03-14
Tests: 116 passing
API: Stable
Contracts: Frozen
Architecture: Documented
```

**PHASE 29 — HYPOTHESIS ENGINE COMPLETE**
