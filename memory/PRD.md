# FOMO Platform — PRD

## Original Problem Statement
TA Engine Module Runtime for Quant Trading Platform with modular architecture.

## Status
- **PHASE 29**: HYPOTHESIS ENGINE V1 FROZEN ✅
- **PHASE 30.1**: HYPOTHESIS POOL ENGINE ✅

---

## Full Market Intelligence OS Architecture

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
│   HYPOTHESIS ENGINE (V1 FROZEN)     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│   HYPOTHESIS COMPETITION (30.1)     │
├─────────────────────────────────────┤
│  • Hypothesis Pool Engine           │
│  • Multi-hypothesis support         │
│  • Ranking & filtering              │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│          Strategy Brain             │
└─────────────────────────────────────┘
    ↓
Strategy Execution
```

---

## PHASE 30.1 — Hypothesis Pool Engine

**PURPOSE:** Transform system from single-hypothesis to multi-hypothesis mode.

**POOL RULES:**
- Max 5 hypotheses per pool
- Confidence threshold: > 0.30
- Reliability threshold: > 0.25
- Execution state != UNFAVORABLE
- NO_EDGE as fallback only

**RANKING SCORE:**
```
ranking_score = 0.50 × confidence + 0.30 × reliability + 0.20 × execution_score
```

**POOL METRICS:**
- `pool_confidence` = mean(top 3 confidences)
- `pool_reliability` = mean(all reliabilities)
- `top_hypothesis` = first in sorted pool

**API ENDPOINTS:**
- `GET /api/v1/hypothesis/pool/{symbol}` — Pool of hypotheses
- `GET /api/v1/hypothesis/pool/summary/{symbol}` — Statistics
- `GET /api/v1/hypothesis/pool/history/{symbol}` — History
- `POST /api/v1/hypothesis/pool/recompute/{symbol}` — Recompute

**TESTS:** 20 pytest + 12 API tests — all passing

---

## Prioritized Backlog

### P0 (Next)
- **PHASE 30.2**: Hypothesis Ranking Engine (diversity penalty, duplicate suppression)
- **PHASE 30.3**: Hypothesis Capital Allocation Engine

### P1
- **PHASE 30.4**: Portfolio Hypothesis Context
- **PHASE 30.5**: Competition Freeze

---

## Test Summary

| Phase | Module | Tests |
|-------|--------|-------|
| 29.2 | Scoring Engine | 25 |
| 29.3 | Conflict Resolver | 20 |
| 29.4 | Registry / History | 22 |
| 29.5 | Strategy Brain | 24 |
| 30.1 | Pool Engine | 20 |
| **Total** | | **111** |

---

## Next Tasks
1. PHASE 30.2 — Hypothesis Ranking Engine
2. PHASE 30.3 — Capital Allocation Engine
3. PHASE 30.4 — Portfolio Hypothesis Context
