# FOMO Platform — PRD

## Original Problem Statement
TA Engine Module Runtime for Quant Trading Platform with modular architecture.

## Architecture
- **Backend**: Python/FastAPI + MongoDB
- **Modules**: Modular quant trading system with 29+ phases
- **Key Components**: Alpha Factory, Regime Intelligence, Microstructure Intelligence, Hypothesis Engine, Strategy Brain

## User Personas
- **Quant Researchers**: Building and validating trading strategies
- **Traders**: Using generated hypotheses and strategy decisions for trading
- **Risk Managers**: Monitoring execution quality, conflicts, and strategy selection

## Core Requirements (Static)
- Market hypothesis generation from intelligence layers
- Scoring separation: idea strength vs execution quality
- Conflict detection and resolution between layers
- Self-protecting system against signal chaos
- Hypothesis-driven strategy selection
- Execution filtering for unfavorable conditions

---

## Implemented Features

### Phase 29.1 — Hypothesis Contract + Core Engine (COMPLETED)
- MarketHypothesis contract
- HypothesisCandidate generation
- Basic scoring with weighted formula

### Phase 29.2 — Hypothesis Scoring Engine (2026-03-14)
- structural_score, execution_score, conflict_score
- confidence/reliability derived from scores
- **TESTS:** 25 unit tests passing

### Phase 29.3 — Hypothesis Conflict Resolver (2026-03-14)
- conflict_state: LOW/MODERATE/HIGH
- Automatic confidence/reliability adjustment
- Execution state downgrade
- **TESTS:** 20 unit tests passing

### Phase 29.4 — Hypothesis Registry / History (2026-03-14)
- MongoDB persistent storage
- Statistics and analytics
- Price tracking for outcome analysis
- **TESTS:** 22 unit tests passing

### Phase 29.5 — Strategy Brain Integration (2026-03-14)
**PURPOSE:** Connect Hypothesis Engine with Strategy Selection.

**HYPOTHESIS → STRATEGY MAPPING:**
- BULLISH_CONTINUATION → trend_following, breakout_trading
- BEARISH_CONTINUATION → trend_following, volatility_expansion
- BREAKOUT_FORMING → breakout_trading, volatility_expansion
- RANGE_MEAN_REVERSION → mean_reversion, range_trading
- NO_EDGE → none

**SUITABILITY SCORE:**
```
suitability_score = 
    0.45 × confidence
  + 0.25 × reliability
  + 0.20 × regime_support
  + 0.10 × microstructure_quality
```

**EXECUTION FILTER:**
- UNFAVORABLE execution_state → strategy blocked (none)

**API ENDPOINTS:**
- `GET /api/v1/strategy/decision/{symbol}` — Strategy decision
- `GET /api/v1/strategy/summary/{symbol}` — Statistics
- `GET /api/v1/strategy/history/{symbol}` — Decision history
- `POST /api/v1/strategy/recompute/{symbol}` — Force recompute
- `GET /api/v1/strategy/available` — Available strategies and mapping

**TESTS:** 24 unit tests passing

---

## Full Market Intelligence OS Architecture

```
Market Data
    ↓
TA Engine + Exchange Intelligence
    ↓
┌─────────────────────────────────────┐
│        Intelligence Layers          │
├─────────────────────────────────────┤
│  Macro-Fractal Layer                │
│  Alpha Factory                      │
│  Regime Intelligence                │
│  Microstructure Intelligence        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│        Hypothesis Engine            │
├─────────────────────────────────────┤
│  Scoring Engine (29.2)              │
│  Conflict Resolver (29.3)           │
│  Registry/History (29.4)            │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│        Strategy Brain (29.5)        │
├─────────────────────────────────────┤
│  Hypothesis → Strategy Mapping      │
│  Suitability Scoring                │
│  Execution Filtering                │
└─────────────────────────────────────┘
    ↓
Strategy Execution
```

---

## Prioritized Backlog

### P0 (Next)
- **Phase 29.6**: Hypothesis Engine Freeze (production-ready)

### P1
- Hypothesis Competition Model (multiple hypotheses competing for capital)
- Hypothesis Outcome Engine (accuracy tracking)

### P2
- Real-time hypothesis streaming via WebSocket
- Strategy performance tracking
- Capital allocation integration

---

## Next Tasks
1. Freeze Hypothesis Engine for production (Phase 29.6)
2. Consider Hypothesis Competition Model for portfolio allocation
3. Add outcome tracking for hypothesis accuracy validation
