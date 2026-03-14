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
- Conflict detection and resolution between layers
- Self-protecting system against signal chaos
- API endpoints for hypothesis management

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

**BEHAVIOR:**
- System becomes self-protecting
- Avoids trading during signal chaos
- Reason includes conflict explanation

**TESTS:** 20 unit tests passing

---

## Prioritized Backlog

### P0 (Next)
- **Phase 29.4**: Hypothesis Registry / History (persistent storage, accuracy analysis)

### P1
- **Phase 29.5**: Hypothesis Integration with Strategy Brain
- **Phase 29.6**: Hypothesis Freeze (production-ready)

### P2
- Hypothesis Competition Model (multiple hypotheses competing for capital)
- Real-time hypothesis streaming via WebSocket
- Future alpha validation based on historical accuracy

---

## Next Tasks
1. Implement Hypothesis Registry with MongoDB persistence (Phase 29.4)
2. Add historical accuracy tracking
3. Integrate with Strategy Brain for trading decisions
