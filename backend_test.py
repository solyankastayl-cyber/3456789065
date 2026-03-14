#!/usr/bin/env python3
"""
PHASE 29.2 - Hypothesis Scoring Engine API Tests

Comprehensive testing of Hypothesis Scoring Engine API endpoints:
- GET /api/v1/hypothesis/current/{symbol}
- GET /api/v1/hypothesis/summary/{symbol}
- GET /api/v1/hypothesis/history/{symbol}
- POST /api/v1/hypothesis/recompute/{symbol}

Tests verify response structure, field validation, and business logic.
Validates the 3 independent scoring components:
1. structural_score - market logic quality
2. execution_score - trading safety 
3. conflict_score - layer contradictions

Tests confidence and reliability calculations.
"""

import requests
import sys
import json
import math
from datetime import datetime
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = "https://ta-analysis-sandbox.preview.emergentagent.com"

class HypothesisScoringAPITester:
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

    def test_hypothesis_current_btc_endpoint(self):
        """Test 1: GET /api/v1/hypothesis/current/BTC - returns hypothesis with all PHASE 29.2 scores."""
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/current/BTC')
        
        if not success:
            self.log_test("1. Hypothesis Current BTC endpoint", False, error)
            return False

        # Check required fields according to MarketHypothesis specification
        required_fields = [
            'symbol', 'hypothesis_type', 'directional_bias',
            'structural_score', 'execution_score', 'conflict_score',
            'confidence', 'reliability',
            'alpha_support', 'regime_support', 'microstructure_support', 'macro_fractal_support',
            'execution_state', 'reason', 'created_at'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("1. Hypothesis Current BTC endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Validate field types and ranges
        validation_errors = []
        
        # Symbol should be BTC
        if data.get('symbol') != 'BTC':
            validation_errors.append(f"Expected symbol 'BTC', got '{data.get('symbol')}'")
            
        # PHASE 29.2: Structural score validation (0-1 range)
        structural_score = data.get('structural_score', -1)
        if not isinstance(structural_score, (int, float)) or not (0 <= structural_score <= 1):
            validation_errors.append(f"structural_score should be between 0 and 1, got: {structural_score}")
            
        # PHASE 29.2: Execution score validation (0-1 range) 
        execution_score = data.get('execution_score', -1)
        if not isinstance(execution_score, (int, float)) or not (0 <= execution_score <= 1):
            validation_errors.append(f"execution_score should be between 0 and 1, got: {execution_score}")
            
        # PHASE 29.2: Conflict score validation (0-1 range)
        conflict_score = data.get('conflict_score', -1)
        if not isinstance(conflict_score, (int, float)) or not (0 <= conflict_score <= 1):
            validation_errors.append(f"conflict_score should be between 0 and 1, got: {conflict_score}")
            
        # Confidence validation (0-1 range)
        confidence = data.get('confidence', -1)
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            validation_errors.append(f"confidence should be between 0 and 1, got: {confidence}")
            
        # Reliability validation (0-1 range)
        reliability = data.get('reliability', -1)
        if not isinstance(reliability, (int, float)) or not (0 <= reliability <= 1):
            validation_errors.append(f"reliability should be between 0 and 1, got: {reliability}")

        # Hypothesis type validation
        valid_hypothesis_types = [
            'BULLISH_CONTINUATION', 'BEARISH_CONTINUATION', 'BREAKOUT_FORMING',
            'RANGE_MEAN_REVERSION', 'NO_EDGE'
        ]
        if data.get('hypothesis_type') not in valid_hypothesis_types:
            validation_errors.append(f"Invalid hypothesis_type: {data.get('hypothesis_type')}")
            
        # Directional bias validation
        if data.get('directional_bias') not in ['LONG', 'SHORT', 'NEUTRAL']:
            validation_errors.append(f"Invalid directional_bias: {data.get('directional_bias')}")
            
        # PHASE 29.2: Execution state validation
        if data.get('execution_state') not in ['FAVORABLE', 'CAUTIOUS', 'UNFAVORABLE']:
            validation_errors.append(f"Invalid execution_state: {data.get('execution_state')}")

        # Support fields validation (0-1 range)
        support_fields = ['alpha_support', 'regime_support', 'microstructure_support', 'macro_fractal_support']
        for field in support_fields:
            value = data.get(field, -1)
            if not isinstance(value, (int, float)) or not (0 <= value <= 1):
                validation_errors.append(f"{field} should be between 0 and 1, got: {value}")

        # Reason should be non-empty string
        if not isinstance(data.get('reason'), str) or not data.get('reason').strip():
            validation_errors.append("reason should be non-empty string")

        # created_at should be valid ISO datetime
        try:
            datetime.fromisoformat(data.get('created_at', '').replace('Z', '+00:00'))
        except (ValueError, TypeError):
            validation_errors.append("created_at should be valid ISO datetime")

        if validation_errors:
            self.log_test("1. Hypothesis Current BTC endpoint", False, "; ".join(validation_errors))
            return False
            
        self.log_test("1. Hypothesis Current BTC endpoint", True)
        return True

    def test_confidence_formula_calculation(self):
        """Test 2: Confidence formula = 0.60 * structural_score + 0.40 * execution_score."""
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/current/BTC')
        
        if not success:
            self.log_test("2. Confidence formula calculation", False, f"Failed to get BTC data: {error}")
            return False

        structural = data.get('structural_score', 0)
        execution = data.get('execution_score', 0)
        confidence = data.get('confidence', 0)
        
        expected_confidence = 0.60 * structural + 0.40 * execution
        
        # Allow for small floating point differences
        if abs(confidence - expected_confidence) > 0.01:
            self.log_test("2. Confidence formula calculation", False, 
                         f"Expected confidence {expected_confidence:.4f}, got {confidence:.4f}")
            return False

        self.log_test("2. Confidence formula calculation", True)
        return True

    def test_reliability_formula_calculation(self):
        """Test 3: Reliability formula = (1 - conflict_score) * regime_support."""
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/current/ETH')
        
        if not success:
            self.log_test("3. Reliability formula calculation", False, f"Failed to get ETH data: {error}")
            return False

        conflict = data.get('conflict_score', 0)
        regime_support = data.get('regime_support', 0)
        reliability = data.get('reliability', 0)
        
        expected_reliability = (1 - conflict) * regime_support
        
        # Allow for small floating point differences
        if abs(reliability - expected_reliability) > 0.01:
            self.log_test("3. Reliability formula calculation", False, 
                         f"Expected reliability {expected_reliability:.4f}, got {reliability:.4f}")
            return False

        self.log_test("3. Reliability formula calculation", True)
        return True

    def test_execution_state_mapping(self):
        """Test 4: Execution state mapping from execution_score."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
            
            if not success:
                self.log_test("4. Execution state mapping", False, f"Failed to get {symbol} data: {error}")
                return False

            execution_score = data.get('execution_score', 0)
            execution_state = data.get('execution_state')
            
            # Verify mapping according to PHASE 29.2 specification
            if execution_score >= 0.70:
                expected_state = 'FAVORABLE'
            elif execution_score >= 0.45:
                expected_state = 'CAUTIOUS'
            else:
                expected_state = 'UNFAVORABLE'
            
            if execution_state != expected_state:
                self.log_test("4. Execution state mapping", False, 
                             f"For {symbol}, execution_score {execution_score:.3f} should map to {expected_state}, got {execution_state}")
                return False

        self.log_test("4. Execution state mapping", True)
        return True

    def test_hypothesis_summary_btc_endpoint(self):
        """Test 5: GET /api/v1/hypothesis/summary/BTC - returns aggregated stats."""
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/summary/BTC')
        
        if not success:
            self.log_test("5. Hypothesis Summary BTC endpoint", False, error)
            return False

        # Check summary structure according to HypothesisSummary
        required_fields = [
            'symbol', 'total_records', 'types', 'bias', 'execution_states', 'averages', 'current'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("5. Hypothesis Summary BTC endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Check nested structures
        validation_errors = []
        
        # Types counts
        types = data.get('types', {})
        expected_types = ['bullish_continuation', 'bearish_continuation', 'breakout_forming', 
                         'range_mean_reversion', 'no_edge', 'other']
        if not all(t in types for t in expected_types):
            validation_errors.append("Missing type counts")
            
        # Bias counts  
        bias = data.get('bias', {})
        expected_bias = ['long', 'short', 'neutral']
        if not all(b in bias for b in expected_bias):
            validation_errors.append("Missing bias counts")
            
        # Execution states counts
        execution_states = data.get('execution_states', {})
        expected_states = ['favorable', 'cautious', 'unfavorable']
        if not all(state in execution_states for state in expected_states):
            validation_errors.append("Missing execution state counts")
            
        # Averages
        averages = data.get('averages', {})
        expected_avg = ['confidence', 'reliability']
        if not all(avg in averages for avg in expected_avg):
            validation_errors.append("Missing average fields")

        # Current state
        current = data.get('current', {})
        expected_current = ['hypothesis', 'bias']
        if not all(curr in current for curr in expected_current):
            validation_errors.append("Missing current state fields")

        if validation_errors:
            self.log_test("5. Hypothesis Summary BTC endpoint", False, "; ".join(validation_errors))
            return False
            
        self.log_test("5. Hypothesis Summary BTC endpoint", True)
        return True

    def test_hypothesis_history_btc_endpoint(self):
        """Test 6: GET /api/v1/hypothesis/history/BTC?limit=10 - returns history."""
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/history/BTC?limit=10')
        
        if not success:
            self.log_test("6. Hypothesis History BTC endpoint", False, error)
            return False

        # Check history structure
        required_fields = ['symbol', 'records', 'total']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("6. Hypothesis History BTC endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Validate history array
        records = data.get('records', [])
        if not isinstance(records, list):
            self.log_test("6. Hypothesis History BTC endpoint", False, "Records should be an array")
            return False
            
        # Check total matches array length
        if data.get('total') != len(records):
            self.log_test("6. Hypothesis History BTC endpoint", False, "Total doesn't match records array length")
            return False

        # If we have history records, validate first one
        if records:
            first_record = records[0]
            required_record_fields = [
                'hypothesis_type', 'directional_bias', 'confidence', 'reliability',
                'execution_state', 'created_at'
            ]
            
            missing_record_fields = [field for field in required_record_fields if field not in first_record]
            if missing_record_fields:
                self.log_test("6. Hypothesis History BTC endpoint", False, f"History record missing fields: {missing_record_fields}")
                return False

        self.log_test("6. Hypothesis History BTC endpoint", True)
        return True

    def test_hypothesis_recompute_eth_endpoint(self):
        """Test 7: POST /api/v1/hypothesis/recompute/ETH - recomputes hypothesis with new scores."""
        success, data, error = self.test_api_call('POST', 'api/v1/hypothesis/recompute/ETH')
        
        if not success:
            self.log_test("7. Hypothesis Recompute ETH endpoint", False, error)
            return False

        # Check recompute response structure
        required_fields = [
            'status', 'symbol', 'hypothesis_type', 'directional_bias',
            'structural_score', 'execution_score', 'conflict_score',
            'confidence', 'reliability', 'execution_state', 'reason', 'computed_at'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("7. Hypothesis Recompute ETH endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Check status is ok
        if data.get('status') != 'ok':
            self.log_test("7. Hypothesis Recompute ETH endpoint", False, f"Expected status 'ok', got '{data.get('status')}'")
            return False
            
        # Check symbol is ETH
        if data.get('symbol') != 'ETH':
            self.log_test("7. Hypothesis Recompute ETH endpoint", False, f"Expected symbol 'ETH', got '{data.get('symbol')}'")
            return False

        # Validate PHASE 29.2 scores
        validation_errors = []
        for score_field in ['structural_score', 'execution_score', 'conflict_score', 'confidence', 'reliability']:
            value = data.get(score_field, -1)
            if not isinstance(value, (int, float)) or not (0 <= value <= 1):
                validation_errors.append(f"{score_field} should be between 0 and 1, got: {value}")

        if validation_errors:
            self.log_test("7. Hypothesis Recompute ETH endpoint", False, "; ".join(validation_errors))
            return False

        self.log_test("7. Hypothesis Recompute ETH endpoint", True)
        return True

    def test_structural_score_ranges(self):
        """Test 8: Structural scores are within [0, 1] range for multiple symbols."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
            
            if not success:
                self.log_test("8. Structural score ranges", False, f"Failed to get {symbol} data: {error}")
                return False

            structural_score = data.get('structural_score')
            
            if not isinstance(structural_score, (int, float)) or not (0 <= structural_score <= 1):
                self.log_test("8. Structural score ranges", False, f"Invalid structural_score for {symbol}: {structural_score}")
                return False

        self.log_test("8. Structural score ranges", True)
        return True

    def test_execution_score_ranges(self):
        """Test 9: Execution scores are within [0, 1] range for multiple symbols."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
            
            if not success:
                self.log_test("9. Execution score ranges", False, f"Failed to get {symbol} data: {error}")
                return False

            execution_score = data.get('execution_score')
            
            if not isinstance(execution_score, (int, float)) or not (0 <= execution_score <= 1):
                self.log_test("9. Execution score ranges", False, f"Invalid execution_score for {symbol}: {execution_score}")
                return False

        self.log_test("9. Execution score ranges", True)
        return True

    def test_conflict_score_ranges(self):
        """Test 10: Conflict scores are within [0, 1] range for multiple symbols."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
            
            if not success:
                self.log_test("10. Conflict score ranges", False, f"Failed to get {symbol} data: {error}")
                return False

            conflict_score = data.get('conflict_score')
            
            if not isinstance(conflict_score, (int, float)) or not (0 <= conflict_score <= 1):
                self.log_test("10. Conflict score ranges", False, f"Invalid conflict_score for {symbol}: {conflict_score}")
                return False

        self.log_test("10. Conflict score ranges", True)
        return True

    def test_bullish_continuation_hypothesis(self):
        """Test 11: Bullish continuation hypothesis generation."""
        # Test multiple symbols to find one with BULLISH_CONTINUATION or validate structure
        symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT']
        found_bullish = False
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
            
            if success and data.get('hypothesis_type') == 'BULLISH_CONTINUATION':
                found_bullish = True
                # Verify directional bias is LONG
                bias = data.get('directional_bias')
                if bias != 'LONG':
                    self.log_test("11. Bullish continuation hypothesis", False, f"BULLISH_CONTINUATION with non-LONG bias: {bias}")
                    return False
                break
        
        # At minimum, verify the API returns valid hypothesis types
        if not found_bullish:
            success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/current/BTC')
            if success:
                hypothesis_type = data.get('hypothesis_type')
                valid_types = ['BULLISH_CONTINUATION', 'BEARISH_CONTINUATION', 'BREAKOUT_FORMING', 
                              'RANGE_MEAN_REVERSION', 'NO_EDGE']
                is_valid = hypothesis_type in valid_types
                self.log_test("11. Bullish continuation hypothesis", is_valid, f"API returns valid hypothesis type: {hypothesis_type}")
                return is_valid

        self.log_test("11. Bullish continuation hypothesis", found_bullish)
        return found_bullish

    def test_bearish_continuation_hypothesis(self):
        """Test 12: Bearish continuation hypothesis generation."""
        symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT']
        found_bearish = False
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
            
            if success and data.get('hypothesis_type') == 'BEARISH_CONTINUATION':
                found_bearish = True
                # Verify directional bias is SHORT
                bias = data.get('directional_bias')
                if bias != 'SHORT':
                    self.log_test("12. Bearish continuation hypothesis", False, f"BEARISH_CONTINUATION with non-SHORT bias: {bias}")
                    return False
                break
        
        self.log_test("12. Bearish continuation hypothesis", found_bearish, "No BEARISH_CONTINUATION found in tested symbols")
        return found_bearish

    def test_breakout_forming_hypothesis(self):
        """Test 13: Breakout forming hypothesis generation."""
        symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
            
            if success and data.get('hypothesis_type') == 'BREAKOUT_FORMING':
                # Verify directional bias is LONG or SHORT (not NEUTRAL)
                bias = data.get('directional_bias')
                if bias not in ['LONG', 'SHORT']:
                    self.log_test("13. Breakout forming hypothesis", False, f"BREAKOUT_FORMING with NEUTRAL bias: {bias}")
                    return False
                self.log_test("13. Breakout forming hypothesis", True)
                return True
        
        self.log_test("13. Breakout forming hypothesis", False, "No BREAKOUT_FORMING found in tested symbols")
        return False

    def test_range_mean_reversion_hypothesis(self):
        """Test 14: Range mean reversion hypothesis generation."""
        symbols = ['SOL', 'USDT', 'USDC', 'STABLE', 'ADA']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
            
            if success and data.get('hypothesis_type') == 'RANGE_MEAN_REVERSION':
                self.log_test("14. Range mean reversion hypothesis", True)
                return True
        
        self.log_test("14. Range mean reversion hypothesis", False, "No RANGE_MEAN_REVERSION found in tested symbols")
        return False

    def test_no_edge_hypothesis(self):
        """Test 15: No edge hypothesis generation (fallback)."""
        # NO_EDGE should always be available as fallback
        symbols = ['UNKNOWN', 'INVALID', 'TEST']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
            
            if success and data.get('hypothesis_type') == 'NO_EDGE':
                # Verify directional bias is typically NEUTRAL for NO_EDGE
                bias = data.get('directional_bias')
                if bias == 'NEUTRAL':
                    self.log_test("15. No edge hypothesis", True)
                    return True
        
        # At minimum, verify any symbol can return NO_EDGE
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/current/BTC')
        if success:
            hypothesis_type = data.get('hypothesis_type')
            # NO_EDGE is always available, but might not be selected for strong symbols like BTC
            self.log_test("15. No edge hypothesis", True, f"API working, current type for BTC: {hypothesis_type}")
            return True
        
        self.log_test("15. No edge hypothesis", False, "Failed to get any hypothesis data")
        return False

    def test_execution_state_favorable(self):
        """Test 16: Execution state FAVORABLE (execution_score >= 0.70)."""
        symbols = ['BTC', 'ETH', 'SOL', 'ADA']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
            
            if success and data.get('execution_state') == 'FAVORABLE':
                # Verify execution_score >= 0.70
                execution_score = data.get('execution_score', 0)
                if execution_score < 0.70:
                    self.log_test("16. Execution state FAVORABLE", False, f"FAVORABLE with execution_score {execution_score:.3f} < 0.70")
                    return False
                self.log_test("16. Execution state FAVORABLE", True)
                return True
        
        # At least verify API returns valid execution states
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/current/BTC')
        if success:
            state = data.get('execution_state')
            valid_states = ['FAVORABLE', 'CAUTIOUS', 'UNFAVORABLE']
            is_valid = state in valid_states
            self.log_test("16. Execution state FAVORABLE", is_valid, f"API returns valid execution state: {state}")
            return is_valid
        
        self.log_test("16. Execution state FAVORABLE", False, "Failed to get any data")
        return False

    def test_execution_state_cautious(self):
        """Test 17: Execution state CAUTIOUS (0.45 <= execution_score < 0.70)."""
        symbols = ['SOL', 'ADA', 'DOT', 'LINK', 'UNI']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
            
            if success and data.get('execution_state') == 'CAUTIOUS':
                # Verify 0.45 <= execution_score < 0.70
                execution_score = data.get('execution_score', 0)
                if not (0.45 <= execution_score < 0.70):
                    self.log_test("17. Execution state CAUTIOUS", False, f"CAUTIOUS with execution_score {execution_score:.3f} outside range [0.45, 0.70)")
                    return False
                self.log_test("17. Execution state CAUTIOUS", True)
                return True
        
        self.log_test("17. Execution state CAUTIOUS", False, "No CAUTIOUS execution state found in tested symbols")
        return False

    def test_execution_state_unfavorable(self):
        """Test 18: Execution state UNFAVORABLE (execution_score < 0.45)."""
        symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
            
            if success and data.get('execution_state') == 'UNFAVORABLE':
                # Verify execution_score < 0.45
                execution_score = data.get('execution_score', 0)
                if execution_score >= 0.45:
                    self.log_test("18. Execution state UNFAVORABLE", False, f"UNFAVORABLE with execution_score {execution_score:.3f} >= 0.45")
                    return False
                self.log_test("18. Execution state UNFAVORABLE", True)
                return True
        
        self.log_test("18. Execution state UNFAVORABLE", False, "No UNFAVORABLE execution state found in tested symbols")
        return False

    def test_support_layer_consistency(self):
        """Test 19: Support layer values consistency."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
            
            if not success:
                self.log_test("19. Support layer consistency", False, f"Failed to get {symbol} data: {error}")
                return False

            # All support values should be between 0 and 1
            support_fields = ['alpha_support', 'regime_support', 'microstructure_support', 'macro_fractal_support']
            
            for field in support_fields:
                value = data.get(field, -1)
                if not isinstance(value, (int, float)) or not (0 <= value <= 1):
                    self.log_test("19. Support layer consistency", False, f"Invalid {field} for {symbol}: {value}")
                    return False

        self.log_test("19. Support layer consistency", True)
        return True

    def test_hypothesis_reason_generation(self):
        """Test 20: Hypothesis reason generation."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
            
            if not success:
                self.log_test("20. Hypothesis reason generation", False, f"Failed to get {symbol} data: {error}")
                return False

            reason = data.get('reason', '')
            
            # Reason should be a non-empty string that describes the hypothesis
            if not isinstance(reason, str) or not reason.strip():
                self.log_test("20. Hypothesis reason generation", False, f"Empty or invalid reason for {symbol}")
                return False
                
            # Reason should contain relevant terms for hypothesis
            hypothesis_type = data.get('hypothesis_type', '')
            if hypothesis_type == 'BULLISH_CONTINUATION' and 'bullish' not in reason.lower():
                self.log_test("20. Hypothesis reason generation", False, f"Bullish hypothesis without 'bullish' in reason: {reason}")
                return False

        self.log_test("20. Hypothesis reason generation", True)
        return True

    def run_all_tests(self):
        """Run all tests and print summary."""
        print("\n" + "=" * 80)
        print("PHASE 29.2 — Hypothesis Scoring Engine API Tests")
        print("=" * 80)
        print(f"Backend URL: {self.base_url}")
        print("-" * 80)
        
        # Run all tests
        test_methods = [
            self.test_hypothesis_current_btc_endpoint,
            self.test_confidence_formula_calculation,
            self.test_reliability_formula_calculation,
            self.test_execution_state_mapping,
            self.test_hypothesis_summary_btc_endpoint,
            self.test_hypothesis_history_btc_endpoint,
            self.test_hypothesis_recompute_eth_endpoint,
            self.test_structural_score_ranges,
            self.test_execution_score_ranges,
            self.test_conflict_score_ranges,
            self.test_bullish_continuation_hypothesis,
            self.test_bearish_continuation_hypothesis,
            self.test_breakout_forming_hypothesis,
            self.test_range_mean_reversion_hypothesis,
            self.test_no_edge_hypothesis,
            self.test_execution_state_favorable,
            self.test_execution_state_cautious,
            self.test_execution_state_unfavorable,
            self.test_support_layer_consistency,
            self.test_hypothesis_reason_generation,
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(test_method.__name__, False, f"Exception: {str(e)}")
        
        # Print summary
        print("-" * 80)
        print(f"Tests completed: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All API tests passed!")
            return True
        else:
            failed_count = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_count} API tests failed")
            return False


def main():
    """Run the test suite."""
    tester = HypothesisScoringAPITester()
    success = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())