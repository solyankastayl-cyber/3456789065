#!/usr/bin/env python3
"""
PHASE 30.1 & 30.2 - Hypothesis Pool & Ranking Engine API Tests

Comprehensive testing of:

PHASE 30.1 - Hypothesis Pool Engine API endpoints:
- GET /api/v1/hypothesis/pool/{symbol} - returns pool of competing hypotheses
- GET /api/v1/hypothesis/pool/summary/{symbol} - returns pool statistics
- GET /api/v1/hypothesis/pool/history/{symbol} - returns pool history
- POST /api/v1/hypothesis/pool/recompute/{symbol} - recomputes pool

PHASE 30.2 - Hypothesis Ranking Engine API endpoints:
- GET /api/v1/hypothesis/ranked/{symbol} - returns ranked pool with diversification
- GET /api/v1/hypothesis/ranked/history/{symbol} - returns ranked pool history
- POST /api/v1/hypothesis/ranked/recompute/{symbol} - recomputes ranked pool

Tests verify:
1. Pool has maximum 5 hypotheses
2. Hypotheses sorted by ranking_score descending
3. top_hypothesis is first in pool
4. Duplicate suppression - only strongest of same type retained
5. Dominance penalty applied when ≥3 hypotheses in same direction (×0.92)
6. Diversity penalty applied when structural scores too similar (×0.95)
7. directional_balance returned in response
8. ranking_metadata with duplicates_removed, dominance_penalty_applied, diversity_penalties_applied
9. Pool confidence and reliability calculations
10. Filtering and ranking score calculations
"""

import requests
import sys
import json
import math
from datetime import datetime
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = "https://ta-analysis-sandbox.preview.emergentagent.com"

class HypothesisPoolAPITester:
    def __init__(self, base_url=BACKEND_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []
        
        # Pool validation constants
        self.MAX_POOL_SIZE = 5
        self.CONFIDENCE_THRESHOLD = 0.30
        self.RELIABILITY_THRESHOLD = 0.25
        self.RANKING_WEIGHT_CONFIDENCE = 0.50
        self.RANKING_WEIGHT_RELIABILITY = 0.30
        self.RANKING_WEIGHT_EXECUTION = 0.20
        self.POOL_CONFIDENCE_TOP_N = 3
        
        # Ranking Engine constants (PHASE 30.2)
        self.DOMINANCE_THRESHOLD = 3
        self.DOMINANCE_PENALTY = 0.92
        self.SIMILARITY_THRESHOLD = 0.05
        self.DIVERSITY_PENALTY = 0.95

    def log_test(self, name: str, passed: bool, details: str = ""):
        """Log test result."""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            status = "PASS"
            icon = "✅"
        else:
            status = f"FAIL: {details}"
            icon = "❌"
        
        self.results.append((name, status))
        print(f"{icon} {name}: {status}")

    def test_api_call(self, method: str, endpoint: str, expected_status: int = 200, data: Dict = None) -> tuple:
        """Make API call and return success status and response."""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method == 'GET':
                response = self.session.get(url)
            elif method == 'POST':
                response = self.session.post(url, json=data)
            else:
                return False, {}, f"Unsupported method: {method}"

            success = response.status_code == expected_status
            
            if success:
                try:
                    json_data = response.json()
                    return True, json_data, ""
                except json.JSONDecodeError:
                    return False, {}, f"Invalid JSON response: {response.text[:200]}"
            else:
                return False, {}, f"Expected {expected_status}, got {response.status_code}: {response.text[:200]}"
                
        except requests.exceptions.RequestException as e:
            return False, {}, f"Request failed: {str(e)}"

    def test_hypothesis_pool_btc_endpoint(self):
        """Test 1: GET /api/v1/hypothesis/pool/BTC - returns pool of competing hypotheses."""
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/pool/BTC')
        
        if not success:
            self.log_test("1. Hypothesis Pool BTC endpoint", False, error)
            return False

        # Check required fields according to HypothesisPool
        required_fields = [
            'symbol', 'hypotheses', 'top_hypothesis',
            'pool_confidence', 'pool_reliability', 
            'pool_size', 'created_at'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("1. Hypothesis Pool BTC endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Validate field types and ranges
        validation_errors = []
        
        # Symbol should be BTC
        if data.get('symbol') != 'BTC':
            validation_errors.append(f"Expected symbol 'BTC', got '{data.get('symbol')}'")
            
        # Pool size validation (0-5)
        pool_size = data.get('pool_size', -1)
        if not isinstance(pool_size, int) or not (0 <= pool_size <= self.MAX_POOL_SIZE):
            validation_errors.append(f"pool_size should be 0-{self.MAX_POOL_SIZE}, got: {pool_size}")
            
        # Pool confidence validation (0-1 range)
        pool_confidence = data.get('pool_confidence', -1)
        if not isinstance(pool_confidence, (int, float)) or not (0 <= pool_confidence <= 1):
            validation_errors.append(f"pool_confidence should be between 0 and 1, got: {pool_confidence}")
            
        # Pool reliability validation (0-1 range)
        pool_reliability = data.get('pool_reliability', -1)
        if not isinstance(pool_reliability, (int, float)) or not (0 <= pool_reliability <= 1):
            validation_errors.append(f"pool_reliability should be between 0 and 1, got: {pool_reliability}")

        # Hypotheses should be an array
        hypotheses = data.get('hypotheses', [])
        if not isinstance(hypotheses, list):
            validation_errors.append("hypotheses should be an array")
        else:
            # Pool size should match hypotheses length
            if len(hypotheses) != pool_size:
                validation_errors.append(f"pool_size ({pool_size}) doesn't match hypotheses length ({len(hypotheses)})")
                
            # Pool should not exceed max size
            if len(hypotheses) > self.MAX_POOL_SIZE:
                validation_errors.append(f"Pool exceeds max size {self.MAX_POOL_SIZE}, got {len(hypotheses)}")

        # Top hypothesis should match first hypothesis if pool is not empty
        if hypotheses:
            first_hypothesis = hypotheses[0].get('hypothesis_type', '')
            top_hypothesis = data.get('top_hypothesis', '')
            if first_hypothesis != top_hypothesis:
                validation_errors.append(f"top_hypothesis ({top_hypothesis}) doesn't match first hypothesis ({first_hypothesis})")
        else:
            # Empty pool should have NO_EDGE as top hypothesis
            if data.get('top_hypothesis') != 'NO_EDGE':
                validation_errors.append(f"Empty pool should have NO_EDGE as top_hypothesis, got: {data.get('top_hypothesis')}")

        # Validate individual hypothesis items if present
        for i, hypothesis in enumerate(hypotheses):
            required_h_fields = [
                'hypothesis_type', 'directional_bias', 'confidence', 
                'reliability', 'structural_score', 'execution_score',
                'conflict_score', 'ranking_score', 'execution_state', 'reason'
            ]
            missing_h_fields = [field for field in required_h_fields if field not in hypothesis]
            if missing_h_fields:
                validation_errors.append(f"Hypothesis {i} missing fields: {missing_h_fields}")
                continue
                
            # Score range validation
            for score_field in ['confidence', 'reliability', 'structural_score', 'execution_score', 'conflict_score', 'ranking_score']:
                value = hypothesis.get(score_field, -1)
                if not isinstance(value, (int, float)) or not (0 <= value <= 1):
                    validation_errors.append(f"Hypothesis {i} {score_field} should be 0-1, got: {value}")

        # created_at should be valid ISO datetime
        try:
            datetime.fromisoformat(data.get('created_at', '').replace('Z', '+00:00'))
        except (ValueError, TypeError):
            validation_errors.append("created_at should be valid ISO datetime")

        if validation_errors:
            self.log_test("1. Hypothesis Pool BTC endpoint", False, "; ".join(validation_errors))
            return False
            
        self.log_test("1. Hypothesis Pool BTC endpoint", True)
        return True

    def test_pool_size_limit(self):
        """Test 2: Verify pool has max 5 hypotheses."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/pool/{symbol}')
            
            if not success:
                self.log_test("2. Pool size limit", False, f"Failed to get {symbol} data: {error}")
                return False

            hypotheses = data.get('hypotheses', [])
            pool_size = data.get('pool_size', 0)
            
            if len(hypotheses) > self.MAX_POOL_SIZE:
                self.log_test("2. Pool size limit", False, 
                             f"{symbol}: Pool exceeds max size {self.MAX_POOL_SIZE}, got {len(hypotheses)}")
                return False
                
            if pool_size != len(hypotheses):
                self.log_test("2. Pool size limit", False, 
                             f"{symbol}: pool_size ({pool_size}) doesn't match hypotheses length ({len(hypotheses)})")
                return False

        self.log_test("2. Pool size limit", True)
        return True

    def test_ranking_score_sorting(self):
        """Test 3: Hypotheses sorted by ranking_score descending."""
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/pool/ETH')
        
        if not success:
            self.log_test("3. Ranking score sorting", False, f"Failed to get ETH data: {error}")
            return False

        hypotheses = data.get('hypotheses', [])
        
        if len(hypotheses) < 2:
            self.log_test("3. Ranking score sorting", True, "Pool has less than 2 hypotheses, cannot verify sorting")
            return True

        # Check if sorted in descending order
        for i in range(len(hypotheses) - 1):
            current_score = hypotheses[i].get('ranking_score', 0)
            next_score = hypotheses[i + 1].get('ranking_score', 0)
            
            if current_score < next_score:
                self.log_test("3. Ranking score sorting", False, 
                             f"Hypotheses not sorted by ranking_score descending: {current_score} < {next_score} at position {i}")
                return False

        self.log_test("3. Ranking score sorting", True)
        return True

    def test_ranking_score_calculation(self):
        """Test 4: ranking_score = 0.50*confidence + 0.30*reliability + 0.20*execution_score."""
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/pool/BTC')
        
        if not success:
            self.log_test("4. Ranking score calculation", False, f"Failed to get BTC data: {error}")
            return False

        hypotheses = data.get('hypotheses', [])
        
        if not hypotheses:
            self.log_test("4. Ranking score calculation", True, "No hypotheses to validate ranking score")
            return True

        # Verify ranking score calculation for each hypothesis
        tolerance = 0.01  # Allow small floating-point differences
        
        for i, hypothesis in enumerate(hypotheses):
            confidence = hypothesis.get('confidence', 0)
            reliability = hypothesis.get('reliability', 0)
            execution_score = hypothesis.get('execution_score', 0)
            ranking_score = hypothesis.get('ranking_score', 0)
            
            expected_score = (
                self.RANKING_WEIGHT_CONFIDENCE * confidence +
                self.RANKING_WEIGHT_RELIABILITY * reliability +
                self.RANKING_WEIGHT_EXECUTION * execution_score
            )
            expected_score = round(min(max(expected_score, 0.0), 1.0), 4)
            
            if abs(ranking_score - expected_score) > tolerance:
                self.log_test("4. Ranking score calculation", False, 
                             f"Hypothesis {i}: ranking_score {ranking_score} != expected {expected_score}")
                return False

        self.log_test("4. Ranking score calculation", True)
        return True

    def test_pool_confidence_calculation(self):
        """Test 5: pool_confidence is mean of top 3 hypotheses confidences."""
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/pool/ETH')
        
        if not success:
            self.log_test("5. Pool confidence calculation", False, f"Failed to get ETH data: {error}")
            return False

        hypotheses = data.get('hypotheses', [])
        pool_confidence = data.get('pool_confidence', 0)
        
        if not hypotheses:
            # Empty pool should have 0 confidence
            if pool_confidence != 0:
                self.log_test("5. Pool confidence calculation", False, 
                             f"Empty pool should have 0 confidence, got {pool_confidence}")
                return False
            self.log_test("5. Pool confidence calculation", True)
            return True

        # Calculate expected pool confidence (mean of top N)
        top_n = min(len(hypotheses), self.POOL_CONFIDENCE_TOP_N)
        top_confidences = [h.get('confidence', 0) for h in hypotheses[:top_n]]
        expected_confidence = round(sum(top_confidences) / len(top_confidences), 4)
        
        tolerance = 0.01
        if abs(pool_confidence - expected_confidence) > tolerance:
            self.log_test("5. Pool confidence calculation", False, 
                         f"pool_confidence {pool_confidence} != expected {expected_confidence}")
            return False

        self.log_test("5. Pool confidence calculation", True)
        return True

    def test_pool_reliability_calculation(self):
        """Test 6: pool_reliability is mean of all hypotheses reliabilities."""
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/pool/SOL')
        
        if not success:
            self.log_test("6. Pool reliability calculation", False, f"Failed to get SOL data: {error}")
            return False

        hypotheses = data.get('hypotheses', [])
        pool_reliability = data.get('pool_reliability', 0)
        
        if not hypotheses:
            # Empty pool should have 0 reliability
            if pool_reliability != 0:
                self.log_test("6. Pool reliability calculation", False, 
                             f"Empty pool should have 0 reliability, got {pool_reliability}")
                return False
            self.log_test("6. Pool reliability calculation", True)
            return True

        # Calculate expected pool reliability (mean of all)
        all_reliabilities = [h.get('reliability', 0) for h in hypotheses]
        expected_reliability = round(sum(all_reliabilities) / len(all_reliabilities), 4)
        
        tolerance = 0.01
        if abs(pool_reliability - expected_reliability) > tolerance:
            self.log_test("6. Pool reliability calculation", False, 
                         f"pool_reliability {pool_reliability} != expected {expected_reliability}")
            return False

        self.log_test("6. Pool reliability calculation", True)
        return True

    def test_filtering_thresholds(self):
        """Test 7: Filtering by confidence > 0.30, reliability > 0.25, execution != UNFAVORABLE."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/pool/{symbol}')
            
            if not success:
                self.log_test("7. Filtering thresholds", False, f"Failed to get {symbol} data: {error}")
                return False

            hypotheses = data.get('hypotheses', [])
            
            for i, hypothesis in enumerate(hypotheses):
                confidence = hypothesis.get('confidence', 0)
                reliability = hypothesis.get('reliability', 0)
                execution_state = hypothesis.get('execution_state', 'UNFAVORABLE')
                
                # Check confidence threshold (unless it's NO_EDGE fallback)
                if hypothesis.get('hypothesis_type') != 'NO_EDGE':
                    if confidence <= self.CONFIDENCE_THRESHOLD:
                        self.log_test("7. Filtering thresholds", False, 
                                     f"{symbol} hypothesis {i}: confidence {confidence} <= threshold {self.CONFIDENCE_THRESHOLD}")
                        return False
                        
                    # Check reliability threshold
                    if reliability <= self.RELIABILITY_THRESHOLD:
                        self.log_test("7. Filtering thresholds", False, 
                                     f"{symbol} hypothesis {i}: reliability {reliability} <= threshold {self.RELIABILITY_THRESHOLD}")
                        return False
                        
                    # Check execution state
                    if execution_state == 'UNFAVORABLE':
                        self.log_test("7. Filtering thresholds", False, 
                                     f"{symbol} hypothesis {i}: execution_state is UNFAVORABLE")
                        return False

        self.log_test("7. Filtering thresholds", True)
        return True

    def test_pool_summary_endpoint(self):
        """Test 8: GET /api/v1/hypothesis/pool/summary/{symbol} - returns pool statistics."""
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/pool/summary/BTC')
        
        if not success:
            self.log_test("8. Pool Summary endpoint", False, error)
            return False

        # Check summary structure according to HypothesisPoolSummary
        required_fields = [
            'symbol', 'total_pools', 'top_hypothesis_distribution', 
            'averages', 'current'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("8. Pool Summary endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Check nested structures
        validation_errors = []
        
        # Averages
        averages = data.get('averages', {})
        expected_avg = ['pool_size', 'pool_confidence', 'pool_reliability']
        missing_avgs = [avg for avg in expected_avg if avg not in averages]
        if missing_avgs:
            validation_errors.append(f"Missing average fields: {missing_avgs}")

        # Current state
        current = data.get('current', {})
        expected_current = ['top_hypothesis', 'pool_size']
        missing_current = [curr for curr in expected_current if curr not in current]
        if missing_current:
            validation_errors.append(f"Missing current state fields: {missing_current}")

        # Total pools should be non-negative integer
        total_pools = data.get('total_pools', -1)
        if not isinstance(total_pools, int) or total_pools < 0:
            validation_errors.append(f"total_pools should be non-negative integer, got: {total_pools}")

        if validation_errors:
            self.log_test("8. Pool Summary endpoint", False, "; ".join(validation_errors))
            return False
            
        self.log_test("8. Pool Summary endpoint", True)
        return True

    def test_pool_history_endpoint(self):
        """Test 9: GET /api/v1/hypothesis/pool/history/{symbol} - returns pool history."""
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/pool/history/ETH?limit=10')
        
        if not success:
            self.log_test("9. Pool History endpoint", False, error)
            return False

        # Check history structure
        required_fields = ['symbol', 'pools', 'total']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("9. Pool History endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Validate history array
        pools = data.get('pools', [])
        if not isinstance(pools, list):
            self.log_test("9. Pool History endpoint", False, "pools should be an array")
            return False
            
        # Check total matches array length
        if data.get('total') != len(pools):
            self.log_test("9. Pool History endpoint", False, "total doesn't match pools array length")
            return False

        # If we have history records, validate first one
        if pools:
            first_pool = pools[0]
            required_pool_fields = [
                'top_hypothesis', 'pool_size', 'pool_confidence', 'pool_reliability',
                'hypotheses', 'created_at'
            ]
            
            missing_pool_fields = [field for field in required_pool_fields if field not in first_pool]
            if missing_pool_fields:
                self.log_test("9. Pool History endpoint", False, f"History pool missing fields: {missing_pool_fields}")
                return False

        self.log_test("9. Pool History endpoint", True)
        return True

    def test_pool_recompute_endpoint(self):
        """Test 10: POST /api/v1/hypothesis/pool/recompute/{symbol} - recomputes pool."""
        success, data, error = self.test_api_call('POST', 'api/v1/hypothesis/pool/recompute/SOL')
        
        if not success:
            self.log_test("10. Pool Recompute endpoint", False, error)
            return False

        # Check recompute response structure
        required_fields = [
            'status', 'symbol', 'hypotheses', 'top_hypothesis',
            'pool_confidence', 'pool_reliability', 'pool_size', 'computed_at'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("10. Pool Recompute endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Check status is ok
        if data.get('status') != 'ok':
            self.log_test("10. Pool Recompute endpoint", False, f"Expected status 'ok', got '{data.get('status')}'")
            return False
            
        # Check symbol is SOL
        if data.get('symbol') != 'SOL':
            self.log_test("10. Pool Recompute endpoint", False, f"Expected symbol 'SOL', got '{data.get('symbol')}'")
            return False

        # Validate pool metrics
        validation_errors = []
        for score_field in ['pool_confidence', 'pool_reliability']:
            value = data.get(score_field, -1)
            if not isinstance(value, (int, float)) or not (0 <= value <= 1):
                validation_errors.append(f"{score_field} should be between 0 and 1, got: {value}")

        # Pool size validation
        pool_size = data.get('pool_size', -1)
        if not isinstance(pool_size, int) or not (0 <= pool_size <= self.MAX_POOL_SIZE):
            validation_errors.append(f"pool_size should be 0-{self.MAX_POOL_SIZE}, got: {pool_size}")

        # Hypotheses should be array
        hypotheses = data.get('hypotheses', [])
        if not isinstance(hypotheses, list):
            validation_errors.append("hypotheses should be an array")
        elif len(hypotheses) != pool_size:
            validation_errors.append(f"hypotheses length ({len(hypotheses)}) doesn't match pool_size ({pool_size})")

        if validation_errors:
            self.log_test("10. Pool Recompute endpoint", False, "; ".join(validation_errors))
            return False

        self.log_test("10. Pool Recompute endpoint", True)
        return True

    def test_top_hypothesis_is_first(self):
        """Test 11: top_hypothesis matches first hypothesis in pool."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/pool/{symbol}')
            
            if not success:
                self.log_test("11. top_hypothesis is first", False, f"Failed to get {symbol} data: {error}")
                return False

            hypotheses = data.get('hypotheses', [])
            top_hypothesis = data.get('top_hypothesis', '')
            
            if hypotheses:
                first_hypothesis = hypotheses[0].get('hypothesis_type', '')
                if first_hypothesis != top_hypothesis:
                    self.log_test("11. top_hypothesis is first", False, 
                                 f"{symbol}: top_hypothesis ({top_hypothesis}) != first hypothesis ({first_hypothesis})")
                    return False
            else:
                # Empty pool should have NO_EDGE as top hypothesis
                if top_hypothesis != 'NO_EDGE':
                    self.log_test("11. top_hypothesis is first", False, 
                                 f"{symbol}: Empty pool should have NO_EDGE, got {top_hypothesis}")
                    return False

        self.log_test("11. top_hypothesis is first", True)
        return True

    def test_no_edge_fallback(self):
        """Test 12: NO_EDGE fallback when no valid hypotheses meet criteria."""
        # Try with a symbol that might not have valid hypotheses
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/pool/INVALID')
        
        if not success:
            # If the API call fails, that's expected for invalid symbols
            self.log_test("12. NO_EDGE fallback", True, "Invalid symbol appropriately rejected")
            return True

        # If it succeeds, check if NO_EDGE is used appropriately
        top_hypothesis = data.get('top_hypothesis', '')
        hypotheses = data.get('hypotheses', [])
        
        if not hypotheses:
            # Empty pool should use NO_EDGE
            if top_hypothesis != 'NO_EDGE':
                self.log_test("12. NO_EDGE fallback", False, 
                             f"Empty pool should use NO_EDGE, got {top_hypothesis}")
                return False
        
        self.log_test("12. NO_EDGE fallback", True)
        return True

    # ═══════════════════════════════════════════════════════════════
    # PHASE 30.2 - Hypothesis Ranking Engine Tests  
    # ═══════════════════════════════════════════════════════════════

    def test_ranked_pool_btc_endpoint(self):
        """Test 13: GET /api/v1/hypothesis/ranked/BTC - returns ranked pool with diversification."""
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/ranked/BTC')
        
        if not success:
            self.log_test("13. Ranked Pool BTC endpoint", False, error)
            return False

        # Check required fields according to RankedHypothesisPool
        required_fields = [
            'symbol', 'hypotheses', 'top_hypothesis',
            'directional_balance', 'pool_confidence', 'pool_reliability', 
            'pool_size', 'ranking_metadata', 'created_at'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("13. Ranked Pool BTC endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Validate ranking_metadata structure
        ranking_metadata = data.get('ranking_metadata', {})
        required_metadata = ['duplicates_removed', 'dominance_penalty_applied', 'diversity_penalties_applied']
        missing_metadata = [field for field in required_metadata if field not in ranking_metadata]
        
        if missing_metadata:
            self.log_test("13. Ranked Pool BTC endpoint", False, f"Missing ranking metadata: {missing_metadata}")
            return False

        # Validate directional_balance structure
        directional_balance = data.get('directional_balance', {})
        expected_directions = ['LONG', 'SHORT', 'NEUTRAL']
        for direction in expected_directions:
            if direction not in directional_balance:
                self.log_test("13. Ranked Pool BTC endpoint", False, f"Missing direction in balance: {direction}")
                return False
            if not isinstance(directional_balance[direction], int) or directional_balance[direction] < 0:
                self.log_test("13. Ranked Pool BTC endpoint", False, f"Invalid balance for {direction}: {directional_balance[direction]}")
                return False

        self.log_test("13. Ranked Pool BTC endpoint", True)
        return True

    def test_ranked_pool_sorting(self):
        """Test 14: Ranked hypotheses sorted by ranking_score descending."""
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/ranked/ETH')
        
        if not success:
            self.log_test("14. Ranked pool sorting", False, f"Failed to get ETH ranked data: {error}")
            return False

        hypotheses = data.get('hypotheses', [])
        
        if len(hypotheses) < 2:
            self.log_test("14. Ranked pool sorting", True, "Pool has less than 2 hypotheses, cannot verify sorting")
            return True

        # Check if sorted in descending order
        for i in range(len(hypotheses) - 1):
            current_score = hypotheses[i].get('ranking_score', 0)
            next_score = hypotheses[i + 1].get('ranking_score', 0)
            
            if current_score < next_score:
                self.log_test("14. Ranked pool sorting", False, 
                             f"Ranked hypotheses not sorted by ranking_score descending: {current_score} < {next_score} at position {i}")
                return False

        self.log_test("14. Ranked pool sorting", True)
        return True

    def test_directional_balance(self):
        """Test 15: directional_balance calculation and return."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/ranked/{symbol}')
            
            if not success:
                self.log_test("15. Directional balance", False, f"Failed to get {symbol} ranked data: {error}")
                return False

            directional_balance = data.get('directional_balance', {})
            hypotheses = data.get('hypotheses', [])
            
            # Count actual directions in hypotheses
            actual_counts = {'LONG': 0, 'SHORT': 0, 'NEUTRAL': 0}
            for hypothesis in hypotheses:
                direction = hypothesis.get('directional_bias', 'NEUTRAL')
                if direction in actual_counts:
                    actual_counts[direction] += 1
                else:
                    actual_counts['NEUTRAL'] += 1
            
            # Compare with directional_balance
            for direction in ['LONG', 'SHORT', 'NEUTRAL']:
                balance_count = directional_balance.get(direction, 0)
                if balance_count != actual_counts[direction]:
                    self.log_test("15. Directional balance", False, 
                                 f"{symbol}: {direction} balance mismatch - expected {actual_counts[direction]}, got {balance_count}")
                    return False

        self.log_test("15. Directional balance", True)
        return True

    def test_ranking_metadata_structure(self):
        """Test 16: ranking_metadata contains duplicates_removed, dominance_penalty_applied, diversity_penalties_applied."""
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/ranked/BTC')
        
        if not success:
            self.log_test("16. Ranking metadata structure", False, f"Failed to get BTC ranked data: {error}")
            return False

        ranking_metadata = data.get('ranking_metadata', {})
        
        # Check duplicates_removed is integer >= 0
        duplicates_removed = ranking_metadata.get('duplicates_removed', -1)
        if not isinstance(duplicates_removed, int) or duplicates_removed < 0:
            self.log_test("16. Ranking metadata structure", False, 
                         f"duplicates_removed should be non-negative integer, got: {duplicates_removed}")
            return False

        # Check dominance_penalty_applied is boolean
        dominance_penalty_applied = ranking_metadata.get('dominance_penalty_applied')
        if not isinstance(dominance_penalty_applied, bool):
            self.log_test("16. Ranking metadata structure", False, 
                         f"dominance_penalty_applied should be boolean, got: {type(dominance_penalty_applied)}")
            return False

        # Check diversity_penalties_applied is integer >= 0
        diversity_penalties_applied = ranking_metadata.get('diversity_penalties_applied', -1)
        if not isinstance(diversity_penalties_applied, int) or diversity_penalties_applied < 0:
            self.log_test("16. Ranking metadata structure", False, 
                         f"diversity_penalties_applied should be non-negative integer, got: {diversity_penalties_applied}")
            return False

        self.log_test("16. Ranking metadata structure", True)
        return True

    def test_max_pool_size_ranked(self):
        """Test 17: Ranked pool respects max 5 hypotheses limit."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/ranked/{symbol}')
            
            if not success:
                self.log_test("17. Max pool size ranked", False, f"Failed to get {symbol} ranked data: {error}")
                return False

            hypotheses = data.get('hypotheses', [])
            pool_size = data.get('pool_size', 0)
            
            if len(hypotheses) > self.MAX_POOL_SIZE:
                self.log_test("17. Max pool size ranked", False, 
                             f"{symbol}: Ranked pool exceeds max size {self.MAX_POOL_SIZE}, got {len(hypotheses)}")
                return False
                
            if pool_size != len(hypotheses):
                self.log_test("17. Max pool size ranked", False, 
                             f"{symbol}: pool_size ({pool_size}) doesn't match hypotheses length ({len(hypotheses)})")
                return False

        self.log_test("17. Max pool size ranked", True)
        return True

    def test_ranked_pool_history_endpoint(self):
        """Test 18: GET /api/v1/hypothesis/ranked/history/{symbol} - returns ranked pool history."""
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/ranked/history/ETH?limit=10')
        
        if not success:
            self.log_test("18. Ranked pool history endpoint", False, error)
            return False

        # Check history structure
        required_fields = ['symbol', 'pools', 'total']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("18. Ranked pool history endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Validate history array
        pools = data.get('pools', [])
        if not isinstance(pools, list):
            self.log_test("18. Ranked pool history endpoint", False, "pools should be an array")
            return False
            
        # Check total matches array length
        if data.get('total') != len(pools):
            self.log_test("18. Ranked pool history endpoint", False, "total doesn't match pools array length")
            return False

        # If we have history records, validate first one
        if pools:
            first_pool = pools[0]
            required_pool_fields = [
                'top_hypothesis', 'directional_balance', 'pool_size', 'pool_confidence', 
                'pool_reliability', 'duplicates_removed', 'dominance_penalty_applied', 
                'diversity_penalties_applied', 'created_at'
            ]
            
            missing_pool_fields = [field for field in required_pool_fields if field not in first_pool]
            if missing_pool_fields:
                self.log_test("18. Ranked pool history endpoint", False, f"History pool missing fields: {missing_pool_fields}")
                return False

        self.log_test("18. Ranked pool history endpoint", True)
        return True

    def test_ranked_pool_recompute_endpoint(self):
        """Test 19: POST /api/v1/hypothesis/ranked/recompute/{symbol} - recomputes ranked pool."""
        success, data, error = self.test_api_call('POST', 'api/v1/hypothesis/ranked/recompute/SOL')
        
        if not success:
            self.log_test("19. Ranked pool recompute endpoint", False, error)
            return False

        # Check recompute response structure
        required_fields = [
            'status', 'symbol', 'hypotheses', 'top_hypothesis',
            'directional_balance', 'pool_size', 'ranking_metadata', 'computed_at'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("19. Ranked pool recompute endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Check status is ok
        if data.get('status') != 'ok':
            self.log_test("19. Ranked pool recompute endpoint", False, f"Expected status 'ok', got '{data.get('status')}'")
            return False
            
        # Check symbol is SOL
        if data.get('symbol') != 'SOL':
            self.log_test("19. Ranked pool recompute endpoint", False, f"Expected symbol 'SOL', got '{data.get('symbol')}'")
            return False

        # Validate recompute response has ranking metadata
        ranking_metadata = data.get('ranking_metadata', {})
        if 'duplicates_removed' not in ranking_metadata:
            self.log_test("19. Ranked pool recompute endpoint", False, "Missing duplicates_removed in ranking_metadata")
            return False

        if 'dominance_penalty_applied' not in ranking_metadata:
            self.log_test("19. Ranked pool recompute endpoint", False, "Missing dominance_penalty_applied in ranking_metadata")
            return False

        if 'diversity_penalties_applied' not in ranking_metadata:
            self.log_test("19. Ranked pool recompute endpoint", False, "Missing diversity_penalties_applied in ranking_metadata")
            return False

        self.log_test("19. Ranked pool recompute endpoint", True)
        return True

    def test_dominance_penalty_logic(self):
        """Test 20: Verify dominance penalty is applied when ≥3 hypotheses in same direction."""
        # Generate multiple pools to find one with dominance
        symbols = ['BTC', 'ETH', 'SOL']
        dominance_found = False
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/ranked/{symbol}')
            
            if not success:
                continue

            hypotheses = data.get('hypotheses', [])
            ranking_metadata = data.get('ranking_metadata', {})
            dominance_penalty_applied = ranking_metadata.get('dominance_penalty_applied', False)
            
            # Count directions
            direction_counts = {'LONG': 0, 'SHORT': 0, 'NEUTRAL': 0}
            for hypothesis in hypotheses:
                direction = hypothesis.get('directional_bias', 'NEUTRAL')
                if direction in direction_counts:
                    direction_counts[direction] += 1
                else:
                    direction_counts['NEUTRAL'] += 1
            
            # Check if any direction has >= 3 hypotheses
            has_dominance = any(count >= self.DOMINANCE_THRESHOLD for count in direction_counts.values())
            
            if has_dominance:
                dominance_found = True
                if not dominance_penalty_applied:
                    self.log_test("20. Dominance penalty logic", False, 
                                 f"{symbol}: Has dominance ({direction_counts}) but penalty not applied")
                    return False
                # If dominance penalty is applied, we can't easily verify the exact score changes
                # since we don't have the original scores, but the metadata indicates it was applied
                break

        if not dominance_found:
            self.log_test("20. Dominance penalty logic", True, "No dominance scenario found to test penalty")
        else:
            self.log_test("20. Dominance penalty logic", True)
        return True

    def test_diversity_penalty_logic(self):
        """Test 21: Verify diversity penalty is applied when structural scores are too similar."""
        # Try multiple symbols to find pools with similar structural scores
        symbols = ['BTC', 'ETH', 'SOL']
        diversity_penalty_found = False
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/ranked/{symbol}')
            
            if not success:
                continue

            hypotheses = data.get('hypotheses', [])
            ranking_metadata = data.get('ranking_metadata', {})
            diversity_penalties_applied = ranking_metadata.get('diversity_penalties_applied', 0)
            
            if len(hypotheses) < 2:
                continue
                
            # Check for similar structural scores
            structural_scores = [h.get('structural_score', 0) for h in hypotheses]
            has_similarity = False
            
            for i in range(len(structural_scores)):
                for j in range(i + 1, len(structural_scores)):
                    diff = abs(structural_scores[i] - structural_scores[j])
                    if diff < self.SIMILARITY_THRESHOLD:
                        has_similarity = True
                        break
                if has_similarity:
                    break
            
            if has_similarity:
                diversity_penalty_found = True
                if diversity_penalties_applied == 0:
                    self.log_test("21. Diversity penalty logic", False, 
                                 f"{symbol}: Has similarity but no diversity penalties applied")
                    return False
                break

        if not diversity_penalty_found:
            self.log_test("21. Diversity penalty logic", True, "No diversity penalty scenario found to test")
        else:
            self.log_test("21. Diversity penalty logic", True)
        return True

    def test_duplicate_suppression_logic(self):
        """Test 22: Verify duplicate suppression removes weaker hypotheses of same type."""
        # Try multiple recomputes to generate scenarios with potential duplicates
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            # Force recompute to potentially generate new data
            recompute_success, recompute_data, _ = self.test_api_call('POST', f'api/v1/hypothesis/ranked/recompute/{symbol}')
            
            if not recompute_success:
                continue
                
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/ranked/{symbol}')
            
            if not success:
                continue

            hypotheses = data.get('hypotheses', [])
            ranking_metadata = data.get('ranking_metadata', {})
            duplicates_removed = ranking_metadata.get('duplicates_removed', 0)
            
            # Check for unique hypothesis types
            hypothesis_types = [h.get('hypothesis_type', '') for h in hypotheses]
            unique_types = set(hypothesis_types)
            
            if len(hypothesis_types) != len(unique_types):
                self.log_test("22. Duplicate suppression logic", False, 
                             f"{symbol}: Found duplicate hypothesis types in final pool")
                return False
                
            # If duplicates were removed, we should have fewer hypotheses than original
            # This is indicated by duplicates_removed > 0
            if duplicates_removed > 0:
                # Good - duplicates were identified and removed
                pass

        self.log_test("22. Duplicate suppression logic", True)
        return True

    def run_all_tests(self):
        """Run all tests and print summary."""
        print("\n" + "=" * 80)
        print("PHASE 30.1 & 30.2 — Hypothesis Pool & Ranking Engine API Tests")
        print("=" * 80)
        print(f"Backend URL: {self.base_url}")
        print("-" * 80)
        
        # PHASE 30.1 - Pool Engine Tests
        print("\n🔵 PHASE 30.1 - Hypothesis Pool Engine Tests")
        print("-" * 50)
        pool_tests = [
            self.test_hypothesis_pool_btc_endpoint,
            self.test_pool_size_limit,
            self.test_ranking_score_sorting,
            self.test_ranking_score_calculation,
            self.test_pool_confidence_calculation,
            self.test_pool_reliability_calculation,
            self.test_filtering_thresholds,
            self.test_pool_summary_endpoint,
            self.test_pool_history_endpoint,
            self.test_pool_recompute_endpoint,
            self.test_top_hypothesis_is_first,
            self.test_no_edge_fallback,
        ]
        
        pool_tests_passed = 0
        for test_method in pool_tests:
            try:
                if test_method():
                    pool_tests_passed += 1
            except Exception as e:
                self.log_test(test_method.__name__, False, f"Exception: {str(e)}")
        
        # PHASE 30.2 - Ranking Engine Tests
        print(f"\n🟢 PHASE 30.2 - Hypothesis Ranking Engine Tests")
        print("-" * 50)
        ranking_tests = [
            self.test_ranked_pool_btc_endpoint,
            self.test_ranked_pool_sorting,
            self.test_directional_balance,
            self.test_ranking_metadata_structure,
            self.test_max_pool_size_ranked,
            self.test_ranked_pool_history_endpoint,
            self.test_ranked_pool_recompute_endpoint,
            self.test_dominance_penalty_logic,
            self.test_diversity_penalty_logic,
            self.test_duplicate_suppression_logic,
        ]
        
        ranking_tests_passed = 0
        for test_method in ranking_tests:
            try:
                if test_method():
                    ranking_tests_passed += 1
            except Exception as e:
                self.log_test(test_method.__name__, False, f"Exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"PHASE 30.1 Pool Engine: {pool_tests_passed}/{len(pool_tests)} passed")
        print(f"PHASE 30.2 Ranking Engine: {ranking_tests_passed}/{len(ranking_tests)} passed")
        print(f"Total: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All Hypothesis Pool & Ranking Engine API tests passed!")
            return True
        else:
            failed_count = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_count} tests failed")
            
            # Print failed tests
            print("\n❌ Failed tests:")
            for test_name, status in self.results:
                if "FAIL" in status:
                    print(f"   - {test_name}: {status}")
            
            return False


def main():
    """Run the test suite."""
    tester = HypothesisPoolAPITester()
    success = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())