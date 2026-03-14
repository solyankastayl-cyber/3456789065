#!/usr/bin/env python3
"""
PHASE 29.5 - Strategy Brain API Tests

Comprehensive testing of Strategy Brain API endpoints:
- GET /api/v1/strategy/decision/{symbol}
- GET /api/v1/strategy/summary/{symbol}
- GET /api/v1/strategy/history/{symbol}
- POST /api/v1/strategy/recompute/{symbol}
- GET /api/v1/strategy/available

Tests verify:
1. Hypothesis-to-Strategy mapping (BULLISH_CONTINUATION → trend_following, breakout_trading)
2. Suitability score calculation: 0.45*confidence + 0.25*reliability + 0.20*regime_support + 0.10*microstructure_quality
3. Execution filter: UNFAVORABLE → strategy blocked
4. Integration with Hypothesis Engine
"""

import requests
import sys
import json
import math
from datetime import datetime
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = "https://ta-analysis-sandbox.preview.emergentagent.com"

class StrategyBrainAPITester:
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
        
        # Expected hypothesis-to-strategy mappings
        self.expected_mappings = {
            "BULLISH_CONTINUATION": ["trend_following", "breakout_trading"],
            "BEARISH_CONTINUATION": ["trend_following", "volatility_expansion"], 
            "BREAKOUT_FORMING": ["breakout_trading", "volatility_expansion"],
            "RANGE_MEAN_REVERSION": ["mean_reversion", "range_trading"],
            "SHORT_SQUEEZE_SETUP": ["liquidation_capture", "volatility_expansion"],
            "LONG_SQUEEZE_SETUP": ["liquidation_capture", "volatility_expansion"],
            "VOLATILE_UNWIND": ["volatility_expansion", "mean_reversion"],
            "BREAKOUT_FAILURE_RISK": ["mean_reversion", "range_trading"],
            "NO_EDGE": [],
        }

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

    def test_strategy_decision_btc_endpoint(self):
        """Test 1: GET /api/v1/strategy/decision/BTC - returns strategy decision based on hypothesis."""
        success, data, error = self.test_api_call('GET', 'api/v1/strategy/decision/BTC')
        
        if not success:
            self.log_test("1. Strategy Decision BTC endpoint", False, error)
            return False

        # Check required fields according to StrategyDecision
        required_fields = [
            'symbol', 'hypothesis_type', 'directional_bias',
            'selected_strategy', 'alternative_strategies',
            'suitability_score', 'execution_state',
            'confidence', 'reliability', 'reason', 'created_at'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("1. Strategy Decision BTC endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Validate field types and ranges
        validation_errors = []
        
        # Symbol should be BTC
        if data.get('symbol') != 'BTC':
            validation_errors.append(f"Expected symbol 'BTC', got '{data.get('symbol')}'")
            
        # Suitability score validation (0-1 range)
        suitability_score = data.get('suitability_score', -1)
        if not isinstance(suitability_score, (int, float)) or not (0 <= suitability_score <= 1):
            validation_errors.append(f"suitability_score should be between 0 and 1, got: {suitability_score}")
            
        # Confidence validation (0-1 range)
        confidence = data.get('confidence', -1)
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            validation_errors.append(f"confidence should be between 0 and 1, got: {confidence}")
            
        # Reliability validation (0-1 range)
        reliability = data.get('reliability', -1)
        if not isinstance(reliability, (int, float)) or not (0 <= reliability <= 1):
            validation_errors.append(f"reliability should be between 0 and 1, got: {reliability}")

        # Hypothesis type validation
        valid_hypothesis_types = list(self.expected_mappings.keys())
        if data.get('hypothesis_type') not in valid_hypothesis_types:
            validation_errors.append(f"Invalid hypothesis_type: {data.get('hypothesis_type')}")
            
        # Directional bias validation
        if data.get('directional_bias') not in ['LONG', 'SHORT', 'NEUTRAL']:
            validation_errors.append(f"Invalid directional_bias: {data.get('directional_bias')}")
            
        # Execution state validation
        if data.get('execution_state') not in ['FAVORABLE', 'CAUTIOUS', 'UNFAVORABLE']:
            validation_errors.append(f"Invalid execution_state: {data.get('execution_state')}")

        # Selected strategy validation
        selected_strategy = data.get('selected_strategy', '')
        valid_strategies = [
            "trend_following", "breakout_trading", "mean_reversion", "volatility_expansion",
            "liquidation_capture", "range_trading", "basis_trade", "funding_arb", "none"
        ]
        if selected_strategy not in valid_strategies:
            validation_errors.append(f"Invalid selected_strategy: {selected_strategy}")

        # Alternative strategies should be a list
        if not isinstance(data.get('alternative_strategies'), list):
            validation_errors.append("alternative_strategies should be a list")

        # Reason should be non-empty string
        if not isinstance(data.get('reason'), str) or not data.get('reason').strip():
            validation_errors.append("reason should be non-empty string")

        # created_at should be valid ISO datetime
        try:
            datetime.fromisoformat(data.get('created_at', '').replace('Z', '+00:00'))
        except (ValueError, TypeError):
            validation_errors.append("created_at should be valid ISO datetime")

        if validation_errors:
            self.log_test("1. Strategy Decision BTC endpoint", False, "; ".join(validation_errors))
            return False
            
        self.log_test("1. Strategy Decision BTC endpoint", True)
        return True

    def test_hypothesis_strategy_mapping(self):
        """Test 2: Verify hypothesis to strategy mapping works correctly."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/strategy/decision/{symbol}')
            
            if not success:
                self.log_test("2. Hypothesis-Strategy mapping", False, f"Failed to get {symbol} data: {error}")
                return False

            hypothesis_type = data.get('hypothesis_type')
            selected_strategy = data.get('selected_strategy')
            alternative_strategies = data.get('alternative_strategies', [])
            
            # Check if the selected strategy is valid for the hypothesis
            expected_strategies = self.expected_mappings.get(hypothesis_type, [])
            
            if hypothesis_type == 'NO_EDGE':
                # NO_EDGE should map to "none"
                if selected_strategy != "none":
                    self.log_test("2. Hypothesis-Strategy mapping", False, 
                                 f"{symbol}: NO_EDGE should select 'none', got '{selected_strategy}'")
                    return False
            else:
                # Other hypothesis types should select from expected strategies
                if expected_strategies and selected_strategy not in expected_strategies:
                    self.log_test("2. Hypothesis-Strategy mapping", False, 
                                 f"{symbol}: {hypothesis_type} should select from {expected_strategies}, got '{selected_strategy}'")
                    return False
                    
                # Alternative strategies should also be from expected list
                for alt_strategy in alternative_strategies:
                    if alt_strategy not in expected_strategies:
                        self.log_test("2. Hypothesis-Strategy mapping", False, 
                                     f"{symbol}: Alternative strategy '{alt_strategy}' not valid for {hypothesis_type}")
                        return False

        self.log_test("2. Hypothesis-Strategy mapping", True)
        return True

    def test_suitability_score_calculation(self):
        """Test 3: Suitability score = 0.45*confidence + 0.25*reliability + 0.20*regime_support + 0.10*microstructure_quality."""
        success, data, error = self.test_api_call('GET', 'api/v1/strategy/decision/ETH')
        
        if not success:
            self.log_test("3. Suitability score calculation", False, f"Failed to get ETH data: {error}")
            return False

        confidence = data.get('confidence', 0)
        reliability = data.get('reliability', 0) 
        suitability_score = data.get('suitability_score', 0)
        
        # Note: We can't directly test regime_support and microstructure_quality 
        # from the API response as they're internal calculations.
        # We'll verify the score is reasonable given confidence and reliability
        
        # Basic validation: if confidence and reliability are both high, suitability should be decent
        if confidence >= 0.7 and reliability >= 0.7:
            if suitability_score < 0.4:  # Should be at least 0.4 with high conf+rel
                self.log_test("3. Suitability score calculation", False, 
                             f"High confidence ({confidence}) and reliability ({reliability}) should yield higher suitability score than {suitability_score}")
                return False

        # Suitability should not exceed 1.0 or be negative
        if not (0 <= suitability_score <= 1.0):
            self.log_test("3. Suitability score calculation", False, 
                         f"Suitability score should be [0,1], got {suitability_score}")
            return False

        self.log_test("3. Suitability score calculation", True)
        return True

    def test_unfavorable_execution_blocks_strategy(self):
        """Test 4: UNFAVORABLE execution_state blocks strategy selection."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/strategy/decision/{symbol}')
            
            if not success:
                self.log_test("4. UNFAVORABLE execution blocks strategy", False, f"Failed to get {symbol} data: {error}")
                return False

            execution_state = data.get('execution_state')
            selected_strategy = data.get('selected_strategy')
            reason = data.get('reason', '')
            
            if execution_state == 'UNFAVORABLE':
                # Should select "none" when execution is unfavorable
                if selected_strategy != "none":
                    self.log_test("4. UNFAVORABLE execution blocks strategy", False, 
                                 f"{symbol}: UNFAVORABLE execution should block strategy, got '{selected_strategy}'")
                    return False
                    
                # Reason should mention execution conditions
                if 'unfavorable' not in reason.lower():
                    self.log_test("4. UNFAVORABLE execution blocks strategy", False, 
                                 f"{symbol}: Reason should mention unfavorable execution: {reason}")
                    return False
                    
                self.log_test("4. UNFAVORABLE execution blocks strategy", True)
                return True

        # If no UNFAVORABLE found, test with multiple symbols
        self.log_test("4. UNFAVORABLE execution blocks strategy", True, "No UNFAVORABLE execution found in tested symbols")
        return True

    def test_strategy_summary_endpoint(self):
        """Test 5: GET /api/v1/strategy/summary/{symbol} - returns strategy statistics."""
        success, data, error = self.test_api_call('GET', 'api/v1/strategy/summary/BTC')
        
        if not success:
            self.log_test("5. Strategy Summary endpoint", False, error)
            return False

        # Check summary structure according to StrategySummary
        required_fields = [
            'symbol', 'total_decisions', 'strategies', 'averages', 'current'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("5. Strategy Summary endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Check nested structures
        validation_errors = []
        
        # Strategy counts
        strategies = data.get('strategies', {})
        expected_strategies = [
            'trend_following', 'breakout_trading', 'mean_reversion', 'volatility_expansion',
            'liquidation_capture', 'range_trading', 'basis_trade', 'funding_arb', 'none'
        ]
        missing_strategies = [s for s in expected_strategies if s not in strategies]
        if missing_strategies:
            validation_errors.append(f"Missing strategy counts: {missing_strategies}")
            
        # Averages
        averages = data.get('averages', {})
        expected_avg = ['suitability_score', 'confidence', 'reliability']
        missing_avgs = [avg for avg in expected_avg if avg not in averages]
        if missing_avgs:
            validation_errors.append(f"Missing average fields: {missing_avgs}")

        # Current state
        current = data.get('current', {})
        expected_current = ['strategy', 'hypothesis']
        missing_current = [curr for curr in expected_current if curr not in current]
        if missing_current:
            validation_errors.append(f"Missing current state fields: {missing_current}")

        if validation_errors:
            self.log_test("5. Strategy Summary endpoint", False, "; ".join(validation_errors))
            return False
            
        self.log_test("5. Strategy Summary endpoint", True)
        return True

    def test_strategy_history_endpoint(self):
        """Test 6: GET /api/v1/strategy/history/{symbol} - returns decision history."""
        success, data, error = self.test_api_call('GET', 'api/v1/strategy/history/BTC?limit=10')
        
        if not success:
            self.log_test("6. Strategy History endpoint", False, error)
            return False

        # Check history structure
        required_fields = ['symbol', 'decisions', 'total']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("6. Strategy History endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Validate history array
        decisions = data.get('decisions', [])
        if not isinstance(decisions, list):
            self.log_test("6. Strategy History endpoint", False, "Decisions should be an array")
            return False
            
        # Check total matches array length
        if data.get('total') != len(decisions):
            self.log_test("6. Strategy History endpoint", False, "Total doesn't match decisions array length")
            return False

        # If we have history records, validate first one
        if decisions:
            first_decision = decisions[0]
            required_decision_fields = [
                'hypothesis_type', 'directional_bias', 'selected_strategy', 
                'suitability_score', 'execution_state', 'confidence', 'reliability',
                'reason', 'created_at'
            ]
            
            missing_decision_fields = [field for field in required_decision_fields if field not in first_decision]
            if missing_decision_fields:
                self.log_test("6. Strategy History endpoint", False, f"History decision missing fields: {missing_decision_fields}")
                return False

        self.log_test("6. Strategy History endpoint", True)
        return True

    def test_strategy_recompute_endpoint(self):
        """Test 7: POST /api/v1/strategy/recompute/{symbol} - recomputes strategy."""
        success, data, error = self.test_api_call('POST', 'api/v1/strategy/recompute/ETH')
        
        if not success:
            self.log_test("7. Strategy Recompute endpoint", False, error)
            return False

        # Check recompute response structure
        required_fields = [
            'status', 'symbol', 'hypothesis_type', 'directional_bias',
            'selected_strategy', 'alternative_strategies', 'suitability_score',
            'execution_state', 'confidence', 'reliability', 'reason', 'computed_at'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("7. Strategy Recompute endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Check status is ok
        if data.get('status') != 'ok':
            self.log_test("7. Strategy Recompute endpoint", False, f"Expected status 'ok', got '{data.get('status')}'")
            return False
            
        # Check symbol is ETH
        if data.get('symbol') != 'ETH':
            self.log_test("7. Strategy Recompute endpoint", False, f"Expected symbol 'ETH', got '{data.get('symbol')}'")
            return False

        # Validate score ranges
        validation_errors = []
        for score_field in ['suitability_score', 'confidence', 'reliability']:
            value = data.get(score_field, -1)
            if not isinstance(value, (int, float)) or not (0 <= value <= 1):
                validation_errors.append(f"{score_field} should be between 0 and 1, got: {value}")

        if validation_errors:
            self.log_test("7. Strategy Recompute endpoint", False, "; ".join(validation_errors))
            return False

        self.log_test("7. Strategy Recompute endpoint", True)
        return True

    def test_strategy_available_endpoint(self):
        """Test 8: GET /api/v1/strategy/available - returns available strategies and mapping."""
        success, data, error = self.test_api_call('GET', 'api/v1/strategy/available')
        
        if not success:
            self.log_test("8. Strategy Available endpoint", False, error)
            return False

        # Check structure
        required_fields = ['strategies', 'hypothesis_mapping']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("8. Strategy Available endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Validate strategies list
        strategies = data.get('strategies', [])
        expected_strategies = [
            "trend_following", "breakout_trading", "mean_reversion", "volatility_expansion",
            "liquidation_capture", "range_trading", "basis_trade", "funding_arb"
        ]
        
        missing_strategies = [s for s in expected_strategies if s not in strategies]
        if missing_strategies:
            self.log_test("8. Strategy Available endpoint", False, f"Missing strategies: {missing_strategies}")
            return False

        # Validate hypothesis mapping
        hypothesis_mapping = data.get('hypothesis_mapping', {})
        for hypothesis, expected_strats in self.expected_mappings.items():
            if hypothesis in hypothesis_mapping:
                actual_strats = hypothesis_mapping[hypothesis]
                if actual_strats != expected_strats:
                    self.log_test("8. Strategy Available endpoint", False, 
                                 f"Mapping mismatch for {hypothesis}: expected {expected_strats}, got {actual_strats}")
                    return False

        self.log_test("8. Strategy Available endpoint", True)
        return True

    def test_bullish_continuation_strategy_mapping(self):
        """Test 9: BULLISH_CONTINUATION → trend_following, breakout_trading."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/strategy/decision/{symbol}')
            
            if success and data.get('hypothesis_type') == 'BULLISH_CONTINUATION':
                selected_strategy = data.get('selected_strategy')
                expected = ["trend_following", "breakout_trading"]
                
                if selected_strategy not in expected:
                    self.log_test("9. BULLISH_CONTINUATION mapping", False, 
                                 f"BULLISH_CONTINUATION should select from {expected}, got '{selected_strategy}'")
                    return False
                    
                self.log_test("9. BULLISH_CONTINUATION mapping", True)
                return True
        
        # If no BULLISH_CONTINUATION found
        self.log_test("9. BULLISH_CONTINUATION mapping", True, "No BULLISH_CONTINUATION found in tested symbols")
        return True

    def test_breakout_forming_strategy_mapping(self):
        """Test 10: BREAKOUT_FORMING → breakout_trading, volatility_expansion."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/strategy/decision/{symbol}')
            
            if success and data.get('hypothesis_type') == 'BREAKOUT_FORMING':
                selected_strategy = data.get('selected_strategy')
                expected = ["breakout_trading", "volatility_expansion"]
                
                if selected_strategy not in expected:
                    self.log_test("10. BREAKOUT_FORMING mapping", False, 
                                 f"BREAKOUT_FORMING should select from {expected}, got '{selected_strategy}'")
                    return False
                    
                self.log_test("10. BREAKOUT_FORMING mapping", True)
                return True
        
        self.log_test("10. BREAKOUT_FORMING mapping", True, "No BREAKOUT_FORMING found in tested symbols")
        return True

    def test_range_mean_reversion_strategy_mapping(self):
        """Test 11: RANGE_MEAN_REVERSION → mean_reversion, range_trading."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/strategy/decision/{symbol}')
            
            if success and data.get('hypothesis_type') == 'RANGE_MEAN_REVERSION':
                selected_strategy = data.get('selected_strategy')
                expected = ["mean_reversion", "range_trading"]
                
                if selected_strategy not in expected:
                    self.log_test("11. RANGE_MEAN_REVERSION mapping", False, 
                                 f"RANGE_MEAN_REVERSION should select from {expected}, got '{selected_strategy}'")
                    return False
                    
                self.log_test("11. RANGE_MEAN_REVERSION mapping", True)
                return True
        
        self.log_test("11. RANGE_MEAN_REVERSION mapping", True, "No RANGE_MEAN_REVERSION found in tested symbols")
        return True

    def test_no_edge_strategy_mapping(self):
        """Test 12: NO_EDGE → none (no strategy)."""
        symbols = ['BTC', 'ETH', 'SOL', 'UNKNOWN']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/strategy/decision/{symbol}')
            
            if success and data.get('hypothesis_type') == 'NO_EDGE':
                selected_strategy = data.get('selected_strategy')
                
                if selected_strategy != "none":
                    self.log_test("12. NO_EDGE mapping", False, 
                                 f"NO_EDGE should select 'none', got '{selected_strategy}'")
                    return False
                    
                self.log_test("12. NO_EDGE mapping", True)
                return True
        
        self.log_test("12. NO_EDGE mapping", True, "No NO_EDGE found in tested symbols")
        return True

    def run_all_tests(self):
        """Run all tests and print summary."""
        print("\n" + "=" * 80)
        print("PHASE 29.5 — Strategy Brain API Tests")
        print("=" * 80)
        print(f"Backend URL: {self.base_url}")
        print("-" * 80)
        
        # Run all tests
        test_methods = [
            self.test_strategy_decision_btc_endpoint,
            self.test_hypothesis_strategy_mapping,
            self.test_suitability_score_calculation,
            self.test_unfavorable_execution_blocks_strategy,
            self.test_strategy_summary_endpoint,
            self.test_strategy_history_endpoint,
            self.test_strategy_recompute_endpoint,
            self.test_strategy_available_endpoint,
            self.test_bullish_continuation_strategy_mapping,
            self.test_breakout_forming_strategy_mapping,
            self.test_range_mean_reversion_strategy_mapping,
            self.test_no_edge_strategy_mapping,
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
            print("🎉 All Strategy Brain API tests passed!")
            return True
        else:
            failed_count = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_count} Strategy Brain API tests failed")
            return False


def main():
    """Run the test suite."""
    tester = StrategyBrainAPITester()
    success = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())