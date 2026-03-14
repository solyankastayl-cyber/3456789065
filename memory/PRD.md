# FOMO Platform — PRD

## Original Problem Statement
TA Engine Module Runtime for Quant Trading Platform with modular architecture.

## Architecture
- **Backend**: Python/FastAPI + MongoDB
- **Modules**: Modular quant trading system with 29+ phases
- **Key Components**: Alpha Factory, Regime Intelligence, Microstructure Intelligence, Hypothesis Engine

## User Personas
- **Quant Researchers**: Building and validating trading strategies
- **Traders**: Using generated hypotheses for trading decisions
- **Risk Managers**: Monitoring execution quality, conflicts, and hypothesis accuracy

## Core Requirements (Static)
- Market hypothesis generation from intelligence layers
- Scoring separation: idea strength vs execution quality
- Conflict detection and resolution between layers
- Self-protecting system against signal chaos
- Persistent hypothesis history for learning and validation
- API endpoints for hypothesis management and analytics

---

## Implemented Features

### Phase 29.1 — Hypothesis Contract + Core Engine (COMPLETED)
- MarketHypothesis contract
- HypothesisCandidate generation
- Basic scoring with weighted formula
- API endpoints: /current, /summary, /history, /recompute

### Phase 29.2 — Hypothesis Scoring Engine (2026-03-14)
**SCORING COMPONENTS:**
1. `structural_score` — Idea quality (alpha 40% + regime 30% + macro 20% + alignment 10%)
2. `execution_score` — Execution safety (microstructure 50% + context 30% + stability 20%)
3. `conflict_score` — Standard deviation of layer support values

**DERIVED SCORES:**
- `confidence` = 0.60 × structural_score + 0.40 × execution_score
- `reliability` = (1 - conflict_score) × regime_support
- `execution_state` derived from execution_score

**TESTS:** 25 unit tests passing

### Phase 29.3 — Hypothesis Conflict Resolver (2026-03-14)
**PURPOSE:** Prevent trading when signals contradict each other.

**CONFLICT STATES:**
- `LOW_CONFLICT` (score < 0.10): No changes
- `MODERATE_CONFLICT` (0.10-0.25): confidence×0.90, reliability×0.90, FAVORABLE→CAUTIOUS
- `HIGH_CONFLICT` (≥0.25): confidence×0.70, reliability×0.75, → UNFAVORABLE

**TESTS:** 20 unit tests passing

### Phase 29.4 — Hypothesis Registry / History (2026-03-14)
**PURPOSE:** Transform Hypothesis Engine from signal generator into market learning system.

**FEATURES:**
- MongoDB persistent storage with all extended fields
- Extended history records with all PHASE 29.2/29.3 scores
- Price tracking (price_at_creation) for future outcome analysis
- Comprehensive statistics and analytics

**NEW API ENDPOINTS:**
- `GET /api/v1/hypothesis/stats/{symbol}` — Full statistics
- `GET /api/v1/hypothesis/recent` — Recent hypotheses across all symbols
- `GET /api/v1/hypothesis/symbols` — List of tracked symbols

**STATISTICS INCLUDE:**
- Directional breakdown (bullish/bearish/neutral)
- Type breakdown (continuation/breakout/mean_reversion)
- Conflict state breakdown (low/moderate/high)
- Execution state breakdown (favorable/cautious/unfavorable)
- Score averages (confidence, reliability, structural, execution, conflict)
- Recent bias trend

**MongoDB Collections:**
- `market_hypothesis_history` — Full hypothesis records
- `market_hypothesis_outcomes` — Structure prepared for future accuracy tracking

**TESTS:** 22 unit tests passing

---

## Prioritized Backlog

### P0 (Next)
- **Phase 29.5**: Hypothesis Integration with Strategy Brain
- **Phase 29.6**: Hypothesis Engine Freeze (production-ready)

### P1
- Hypothesis Competition Model (multiple hypotheses competing for capital)
- Hypothesis Outcome Engine (accuracy tracking and validation)

### P2
- Real-time hypothesis streaming via WebSocket
- Future alpha validation based on historical accuracy
- Hypothesis Analytics Dashboard

---

## Next Tasks
1. Integrate Hypothesis Engine with Strategy Brain (Phase 29.5)
2. Freeze Hypothesis Engine for production (Phase 29.6)
3. Consider Hypothesis Competition Model for portfolio allocation
