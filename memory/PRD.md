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
- **Risk Managers**: Monitoring execution quality and conflicts

## Core Requirements (Static)
- Market hypothesis generation from intelligence layers
- Scoring separation: idea strength vs execution quality
- Conflict detection between layers
- API endpoints for hypothesis management

---

## Implemented Features

### Phase 29.1 — Hypothesis Contract + Core Engine (COMPLETED)
- MarketHypothesis contract
- HypothesisCandidate generation
- Basic scoring with weighted formula
- API endpoints: /current, /summary, /history, /recompute

### Phase 29.2 — Hypothesis Scoring Engine (2026-03-14)
**NEW SCORING COMPONENTS:**
1. `structural_score` — How market-logically sound is the idea (0.40 alpha + 0.30 regime + 0.20 macro + 0.10 alignment)
2. `execution_score` — How safe is it to trade now (0.50 microstructure + 0.30 context + 0.20 stability)
3. `conflict_score` — Standard deviation of layer support values

**DERIVED SCORES:**
- `confidence` = 0.60 * structural_score + 0.40 * execution_score
- `reliability` = (1 - conflict_score) * regime_support
- `execution_state` derived from execution_score (FAVORABLE >= 0.70, CAUTIOUS 0.45-0.70, UNFAVORABLE < 0.45)

**TESTS:** 25 unit tests passing

---

## Prioritized Backlog

### P0 (Next)
- **Phase 29.3**: Hypothesis Conflict Resolver
- **Phase 29.4**: Hypothesis Registry (persistent storage)

### P1
- **Phase 29.5**: Hypothesis Integration with Strategy Brain
- **Phase 29.6**: Hypothesis Freeze (production-ready)

### P2
- Hypothesis Competition Model (multiple hypotheses competing for capital)
- Real-time hypothesis streaming via WebSocket

---

## Next Tasks
1. Implement Hypothesis Conflict Resolver (Phase 29.3)
2. Add persistent hypothesis storage with MongoDB
3. Integrate with Strategy Brain for trading decisions
