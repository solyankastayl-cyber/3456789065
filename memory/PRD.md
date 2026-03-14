# TA Engine PRD — PHASE 29.1 Hypothesis Engine

## Previous Phases
- PHASE 28 — Microstructure Intelligence v2: COMPLETE (88/88 tests)
- Architecture Freeze: 2026-03-13

## Current Phase
- PHASE 29 — Hypothesis Engine: IN PROGRESS

## Problem Statement
Создать Hypothesis Engine — слой генерации рыночных гипотез на основе сигналов
из всех intelligence layers (Alpha, Regime, Microstructure, MacroFractal).

## Architecture

### Module Structure
```
/app/backend/modules/hypothesis_engine/
├── __init__.py
├── hypothesis_types.py         # 29.1 Contracts
├── hypothesis_engine.py        # 29.1 Core Engine
├── hypothesis_registry.py      # 29.1 MongoDB Registry
├── hypothesis_routes.py        # 29.1 API Routes
└── hypothesis_tests.py         # 29.1 Tests
```

## Implemented Phases

### PHASE 28 — Microstructure Intelligence v2 (FROZEN)
- 28.1: Microstructure Snapshot Engine (16/16 tests)
- 28.2: Liquidity Vacuum Detector (18/18 tests)
- 28.3: Orderbook Pressure Map (18/18 tests)
- 28.4: Liquidation Cascade Probability (18/18 tests)
- 28.5: Microstructure Context Integration (18/18 tests)
- **Total: 88/88 tests**

### PHASE 29.1 — Hypothesis Contract + Core Engine ✅
- MarketHypothesis contract with 9 hypothesis types
- HypothesisCandidate internal object
- HypothesisInputLayers from 5 intelligence sources
- Candidate generators: BULLISH_CONTINUATION, BEARISH_CONTINUATION, BREAKOUT_FORMING, RANGE_MEAN_REVERSION, NO_EDGE
- Scoring: raw_score = 0.40*alpha + 0.30*regime + 0.20*micro + 0.10*macro
- Confidence = raw_score clipped [0,1]
- Reliability = 1 - std(alpha, regime, micro) clipped [0,1]
- Execution state mapping: SUPPORTIVE→FAVORABLE, NEUTRAL→CAUTIOUS, FRAGILE/STRESSED→UNFAVORABLE
- MongoDB registry (market_hypothesis_history)
- 4 API endpoints
- **18/18 unit tests + 26/26 API tests passing**

## API Endpoints

### PHASE 29.1 — Hypothesis Engine (4 endpoints)
```
GET  /api/v1/hypothesis/current/{symbol}
GET  /api/v1/hypothesis/history/{symbol}
GET  /api/v1/hypothesis/summary/{symbol}
POST /api/v1/hypothesis/recompute/{symbol}
```

## MongoDB Collections
- market_hypothesis_history (NEW in 29.1)
- microstructure_snapshot_history
- liquidity_vacuum_history
- orderbook_pressure_history
- liquidation_cascade_history

## Test Summary
| Phase | Tests | Status |
|-------|-------|--------|
| 28.1 | 16/16 | ✅ |
| 28.2 | 18/18 | ✅ |
| 28.3 | 18/18 | ✅ |
| 28.4 | 18/18 | ✅ |
| 28.5 | 18/18 | ✅ |
| 29.1 | 18/18 + 26 API | ✅ |

## Scoring Constants (PHASE 29.1)
- WEIGHT_ALPHA = 0.40
- WEIGHT_REGIME = 0.30
- WEIGHT_MICROSTRUCTURE = 0.20
- WEIGHT_MACRO = 0.10

## Upcoming Tasks
- **P0: TASK 77 / PHASE 29.2** — Hypothesis Scoring Engine (structural/execution/conflict scores)
- **P1: PHASE 29.3** — Hypothesis Conflict Resolver
- **P1: PHASE 29.4** — Hypothesis Registry / History
- **P1: PHASE 29.5** — Hypothesis API + Integration
- **P1: PHASE 29.6** — Hypothesis Freeze

## Future Phases
- PHASE 30 — Strategy Brain
- PHASE 31 — Execution Brain
