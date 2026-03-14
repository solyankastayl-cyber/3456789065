#!/usr/bin/env python3
"""
PHASE 29.4 - Hypothesis Registry API Tests

Comprehensive testing of PHASE 29.4 Hypothesis Registry endpoints:
- GET /api/v1/hypothesis/current/{symbol} - stores hypothesis and returns data
- GET /api/v1/hypothesis/history/{symbol} - returns extended history with all scores
- GET /api/v1/hypothesis/stats/{symbol} - returns comprehensive statistics
- GET /api/v1/hypothesis/recent - returns recent hypotheses across all symbols
- GET /api/v1/hypothesis/symbols - returns list of tracked symbols  
- POST /api/v1/hypothesis/recompute/{symbol} - stores and returns hypothesis

Tests verify:
- MongoDB persistence with extended fields
- All PHASE 29.2/29.3 scores (structural_score, execution_score, conflict_score, conflict_state)
- Statistics and analytics functionality
- Cross-symbol monitoring
- Price tracking for future outcome analysis
"""

import requests
import sys
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = "https://ta-analysis-sandbox.preview.emergentagent.com"

class HypothesisRegistryAPITester:
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
        self.test_symbols = ['BTC', 'ETH', 'SOL']

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

    def test_hypothesis_current_with_storage(self):
        """Test 1: GET /api/v1/hypothesis/current/{symbol} - stores hypothesis and returns extended data."""
        symbol = 'BTC'
        success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
        
        if not success:
            self.log_test("1. Hypothesis Current with Storage", False, error)
            return False

        # Check all PHASE 29.4 extended fields
        required_fields = [
            'symbol', 'hypothesis_type', 'directional_bias',
            # PHASE 29.2 scores
            'structural_score', 'execution_score', 'conflict_score',
            # PHASE 29.3 conflict state
            'conflict_state',
            # Core scores
            'confidence', 'reliability', 'execution_state',
            # Support layers
            'alpha_support', 'regime_support', 'microstructure_support', 'macro_fractal_support',
            'reason', 'created_at'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("1. Hypothesis Current with Storage", False, f"Missing fields: {missing_fields}")
            return False

        # Validate field types and ranges
        validation_errors = []
        
        # Score validations (0-1 range)
        score_fields = ['structural_score', 'execution_score', 'conflict_score', 'confidence', 'reliability']
        for field in score_fields:
            value = data.get(field, -1)
            if not isinstance(value, (int, float)) or not (0 <= value <= 1):
                validation_errors.append(f"{field} should be between 0 and 1, got: {value}")
        
        # Conflict state validation
        conflict_state = data.get('conflict_state', '')
        valid_conflict_states = ['LOW_CONFLICT', 'MODERATE_CONFLICT', 'HIGH_CONFLICT']
        if conflict_state not in valid_conflict_states:
            validation_errors.append(f"Invalid conflict_state: {conflict_state}")

        if validation_errors:
            self.log_test("1. Hypothesis Current with Storage", False, "; ".join(validation_errors))
            return False
            
        self.log_test("1. Hypothesis Current with Storage", True)
        return True

    def test_hypothesis_history_extended_fields(self):
        """Test 2: GET /api/v1/hypothesis/history/{symbol} - returns extended history with all scores."""
        # First generate some history by calling current endpoint
        for symbol in self.test_symbols:
            self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
            time.sleep(0.1)  # Small delay between calls

        # Now test history endpoint
        symbol = 'BTC'
        success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/history/{symbol}?limit=5')
        
        if not success:
            self.log_test("2. Hypothesis History Extended Fields", False, error)
            return False

        # Check history structure
        required_fields = ['symbol', 'total', 'records']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("2. Hypothesis History Extended Fields", False, f"Missing fields: {missing_fields}")
            return False

        records = data.get('records', [])
        if not isinstance(records, list):
            self.log_test("2. Hypothesis History Extended Fields", False, "Records should be an array")
            return False

        # Validate extended fields in history records
        if records:
            first_record = records[0]
            extended_fields = [
                'hypothesis_type', 'directional_bias',
                # PHASE 29.2/29.3 scores
                'structural_score', 'execution_score', 'conflict_score', 'conflict_state',
                # Core scores
                'confidence', 'reliability', 'execution_state',
                # PHASE 29.4 price tracking
                'price_at_creation', 'created_at'
            ]
            
            missing_extended_fields = [field for field in extended_fields if field not in first_record]
            if missing_extended_fields:
                self.log_test("2. Hypothesis History Extended Fields", False, f"History record missing extended fields: {missing_extended_fields}")
                return False

            # Validate extended score fields
            validation_errors = []
            score_fields = ['structural_score', 'execution_score', 'conflict_score', 'confidence', 'reliability']
            for field in score_fields:
                value = first_record.get(field, -1)
                if not isinstance(value, (int, float)) or not (0 <= value <= 1):
                    validation_errors.append(f"History record {field} should be between 0 and 1, got: {value}")

            if validation_errors:
                self.log_test("2. Hypothesis History Extended Fields", False, "; ".join(validation_errors))
                return False

        self.log_test("2. Hypothesis History Extended Fields", True)
        return True

    def test_hypothesis_stats_endpoint(self):
        """Test 3: GET /api/v1/hypothesis/stats/{symbol} - returns comprehensive statistics."""
        # Generate some history first
        symbol = 'BTC'
        for _ in range(3):
            self.test_api_call('POST', f'api/v1/hypothesis/recompute/{symbol}')
            time.sleep(0.1)

        success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/stats/{symbol}')
        
        if not success:
            self.log_test("3. Hypothesis Stats Endpoint", False, error)
            return False

        # Check stats structure
        required_fields = [
            'symbol', 'total_hypotheses', 'directional', 'types', 
            'conflict_states', 'execution_states', 'averages', 'recent_bias_trend'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            self.log_test("3. Hypothesis Stats Endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Validate nested structures
        validation_errors = []
        
        # Directional breakdown
        directional = data.get('directional', {})
        expected_directional = ['bullish', 'bearish', 'neutral']
        for field in expected_directional:
            if field not in directional:
                validation_errors.append(f"Missing directional field: {field}")
            elif not isinstance(directional[field], int) or directional[field] < 0:
                validation_errors.append(f"Directional {field} should be non-negative integer")

        # Type breakdown
        types = data.get('types', {})
        expected_types = ['bullish_continuation', 'bearish_continuation', 'breakout_forming', 'range_mean_reversion', 'no_edge']
        for field in expected_types:
            if field not in types:
                validation_errors.append(f"Missing type field: {field}")
            elif not isinstance(types[field], int) or types[field] < 0:
                validation_errors.append(f"Type {field} should be non-negative integer")

        # Conflict states breakdown
        conflict_states = data.get('conflict_states', {})
        expected_conflict = ['low', 'moderate', 'high']
        for field in expected_conflict:
            if field not in conflict_states:
                validation_errors.append(f"Missing conflict state field: {field}")

        # Execution states breakdown  
        execution_states = data.get('execution_states', {})
        expected_execution = ['favorable', 'cautious', 'unfavorable']
        for field in expected_execution:
            if field not in execution_states:
                validation_errors.append(f"Missing execution state field: {field}")

        # Averages - all PHASE 29.2/29.3 scores
        averages = data.get('averages', {})
        expected_averages = ['confidence', 'reliability', 'structural_score', 'execution_score', 'conflict_score']
        for field in expected_averages:
            if field not in averages:
                validation_errors.append(f"Missing average field: {field}")
            elif not isinstance(averages[field], (int, float)) or not (0 <= averages[field] <= 1):
                validation_errors.append(f"Average {field} should be between 0 and 1")

        # Recent bias trend
        recent_trend = data.get('recent_bias_trend', '')
        valid_trends = ['BULLISH', 'BEARISH', 'NEUTRAL']
        if recent_trend not in valid_trends:
            validation_errors.append(f"Invalid recent_bias_trend: {recent_trend}")

        if validation_errors:
            self.log_test("3. Hypothesis Stats Endpoint", False, "; ".join(validation_errors))
            return False

        self.log_test("3. Hypothesis Stats Endpoint", True)
        return True

    def test_hypothesis_recent_endpoint(self):
        """Test 4: GET /api/v1/hypothesis/recent - returns recent hypotheses across all symbols."""
        # Generate history across multiple symbols
        for symbol in self.test_symbols:
            self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
            time.sleep(0.1)

        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/recent?limit=10')
        
        if not success:
            self.log_test("4. Hypothesis Recent Endpoint", False, error)
            return False

        # Check recent structure
        required_fields = ['total', 'limit', 'hypotheses']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("4. Hypothesis Recent Endpoint", False, f"Missing fields: {missing_fields}")
            return False

        hypotheses = data.get('hypotheses', [])
        if not isinstance(hypotheses, list):
            self.log_test("4. Hypothesis Recent Endpoint", False, "Hypotheses should be an array")
            return False

        # Validate hypotheses contain extended fields
        if hypotheses:
            first_hypothesis = hypotheses[0]
            extended_fields = [
                'symbol', 'hypothesis_type', 'directional_bias',
                'structural_score', 'execution_score', 'conflict_score', 'conflict_state',
                'confidence', 'reliability', 'execution_state',
                'price_at_creation', 'created_at'
            ]
            
            missing_extended_fields = [field for field in extended_fields if field not in first_hypothesis]
            if missing_extended_fields:
                self.log_test("4. Hypothesis Recent Endpoint", False, f"Recent hypothesis missing fields: {missing_extended_fields}")
                return False

            # Check symbols are from our test set
            symbols_found = set(h.get('symbol', '') for h in hypotheses)
            expected_symbols = set(self.test_symbols)
            if not symbols_found.intersection(expected_symbols):
                self.log_test("4. Hypothesis Recent Endpoint", False, f"No test symbols found in recent hypotheses: {symbols_found}")
                return False

        # Verify limit parameter works
        if len(hypotheses) > data.get('limit', 0):
            self.log_test("4. Hypothesis Recent Endpoint", False, f"Returned {len(hypotheses)} hypotheses, limit was {data.get('limit')}")
            return False

        self.log_test("4. Hypothesis Recent Endpoint", True)
        return True

    def test_hypothesis_symbols_endpoint(self):
        """Test 5: GET /api/v1/hypothesis/symbols - returns list of tracked symbols."""
        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/symbols')
        
        if not success:
            self.log_test("5. Hypothesis Symbols Endpoint", False, error)
            return False

        # Check symbols structure
        required_fields = ['total', 'symbols']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("5. Hypothesis Symbols Endpoint", False, f"Missing fields: {missing_fields}")
            return False

        symbols = data.get('symbols', [])
        if not isinstance(symbols, list):
            self.log_test("5. Hypothesis Symbols Endpoint", False, "Symbols should be an array")
            return False

        # Verify total matches array length
        if data.get('total') != len(symbols):
            self.log_test("5. Hypothesis Symbols Endpoint", False, f"Total {data.get('total')} doesn't match symbols array length {len(symbols)}")
            return False

        # Check that our test symbols are included
        symbols_set = set(symbols)
        expected_symbols = set(self.test_symbols)
        if not expected_symbols.issubset(symbols_set):
            missing_test_symbols = expected_symbols - symbols_set
            self.log_test("5. Hypothesis Symbols Endpoint", False, f"Missing expected test symbols: {missing_test_symbols}")
            return False

        self.log_test("5. Hypothesis Symbols Endpoint", True)
        return True

    def test_hypothesis_recompute_with_storage(self):
        """Test 6: POST /api/v1/hypothesis/recompute/{symbol} - stores and returns hypothesis."""
        symbol = 'ETH'
        success, data, error = self.test_api_call('POST', f'api/v1/hypothesis/recompute/{symbol}')
        
        if not success:
            self.log_test("6. Hypothesis Recompute with Storage", False, error)
            return False

        # Check recompute response has all extended fields
        required_fields = [
            'status', 'symbol', 'hypothesis_type', 'directional_bias',
            'structural_score', 'execution_score', 'conflict_score', 'conflict_state',
            'confidence', 'reliability', 'execution_state', 'reason', 'computed_at'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            self.log_test("6. Hypothesis Recompute with Storage", False, f"Missing fields: {missing_fields}")
            return False

        # Verify storage worked by checking history
        time.sleep(0.2)  # Small delay for storage
        history_success, history_data, _ = self.test_api_call('GET', f'api/v1/hypothesis/history/{symbol}?limit=1')
        
        if history_success and history_data.get('records'):
            latest_record = history_data['records'][0]
            # Check that the latest record has the same data as the recompute response
            if latest_record.get('hypothesis_type') != data.get('hypothesis_type'):
                self.log_test("6. Hypothesis Recompute with Storage", False, "Recomputed hypothesis not stored correctly")
                return False
        else:
            self.log_test("6. Hypothesis Recompute with Storage", False, "Failed to verify storage in history")
            return False

        self.log_test("6. Hypothesis Recompute with Storage", True)
        return True

    def test_mongodb_persistence_fields(self):
        """Test 7: Verify MongoDB persistence includes all extended fields."""
        symbol = 'SOL'
        
        # Generate hypothesis
        success, current_data, error = self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
        if not success:
            self.log_test("7. MongoDB Persistence Fields", False, f"Failed to generate hypothesis: {error}")
            return False

        # Wait for storage
        time.sleep(0.2)

        # Retrieve from history to verify persistence
        history_success, history_data, history_error = self.test_api_call('GET', f'api/v1/hypothesis/history/{symbol}?limit=1')
        
        if not history_success:
            self.log_test("7. MongoDB Persistence Fields", False, f"Failed to retrieve history: {history_error}")
            return False

        records = history_data.get('records', [])
        if not records:
            self.log_test("7. MongoDB Persistence Fields", False, "No records found in history")
            return False

        latest_record = records[0]
        
        # Verify all PHASE 29.2/29.3/29.4 fields are persisted
        persistent_fields = [
            'hypothesis_type', 'directional_bias',
            'structural_score', 'execution_score', 'conflict_score', 'conflict_state',
            'confidence', 'reliability', 'execution_state',
            'price_at_creation'  # PHASE 29.4 price tracking
        ]
        
        validation_errors = []
        for field in persistent_fields:
            if field not in latest_record:
                validation_errors.append(f"Field {field} not persisted in MongoDB")
            elif field in ['structural_score', 'execution_score', 'conflict_score', 'confidence', 'reliability']:
                # Verify score fields are numbers in correct range
                value = latest_record[field]
                if not isinstance(value, (int, float)) or not (0 <= value <= 1):
                    validation_errors.append(f"Persisted {field} has invalid value: {value}")

        if validation_errors:
            self.log_test("7. MongoDB Persistence Fields", False, "; ".join(validation_errors))
            return False

        self.log_test("7. MongoDB Persistence Fields", True)
        return True

    def test_cross_symbol_statistics(self):
        """Test 8: Statistics work correctly across multiple symbols."""
        symbols_to_test = ['BTC', 'ETH', 'SOL']
        
        # Generate multiple hypotheses per symbol
        for symbol in symbols_to_test:
            for _ in range(2):
                self.test_api_call('POST', f'api/v1/hypothesis/recompute/{symbol}')
                time.sleep(0.1)

        # Test stats for each symbol
        all_symbols_have_stats = True
        
        for symbol in symbols_to_test:
            success, stats_data, error = self.test_api_call('GET', f'api/v1/hypothesis/stats/{symbol}')
            
            if not success:
                self.log_test("8. Cross-Symbol Statistics", False, f"Failed to get stats for {symbol}: {error}")
                return False

            total_hypotheses = stats_data.get('total_hypotheses', 0)
            if total_hypotheses < 1:
                all_symbols_have_stats = False
                self.log_test("8. Cross-Symbol Statistics", False, f"No hypotheses found for {symbol}")
                return False

            # Verify averages are calculated correctly
            averages = stats_data.get('averages', {})
            required_averages = ['confidence', 'reliability', 'structural_score', 'execution_score', 'conflict_score']
            for avg_field in required_averages:
                if avg_field not in averages:
                    self.log_test("8. Cross-Symbol Statistics", False, f"Missing average {avg_field} for {symbol}")
                    return False

        self.log_test("8. Cross-Symbol Statistics", True)
        return True

    def test_recent_hypotheses_sorting(self):
        """Test 9: Recent hypotheses are properly sorted by creation time."""
        # Generate hypotheses with small delays to ensure different timestamps
        for symbol in ['BTC', 'ETH']:
            self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
            time.sleep(0.2)

        success, data, error = self.test_api_call('GET', 'api/v1/hypothesis/recent?limit=5')
        
        if not success:
            self.log_test("9. Recent Hypotheses Sorting", False, error)
            return False

        hypotheses = data.get('hypotheses', [])
        if len(hypotheses) < 2:
            self.log_test("9. Recent Hypotheses Sorting", False, "Need at least 2 hypotheses to test sorting")
            return False

        # Verify chronological order (most recent first)
        for i in range(len(hypotheses) - 1):
            current_time = hypotheses[i].get('created_at', '')
            next_time = hypotheses[i + 1].get('created_at', '')
            
            try:
                current_dt = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
                next_dt = datetime.fromisoformat(next_time.replace('Z', '+00:00'))
                
                if current_dt < next_dt:
                    self.log_test("9. Recent Hypotheses Sorting", False, f"Sorting error: {current_time} < {next_time}")
                    return False
            except ValueError:
                self.log_test("9. Recent Hypotheses Sorting", False, f"Invalid timestamp format: {current_time} or {next_time}")
                return False

        self.log_test("9. Recent Hypotheses Sorting", True)
        return True

    def test_price_tracking_feature(self):
        """Test 10: Price tracking is included in hypothesis storage."""
        symbol = 'BTC'
        
        # Generate hypothesis
        success, data, error = self.test_api_call('GET', f'api/v1/hypothesis/current/{symbol}')
        if not success:
            self.log_test("10. Price Tracking Feature", False, error)
            return False

        # Check history for price tracking
        time.sleep(0.2)
        history_success, history_data, _ = self.test_api_call('GET', f'api/v1/hypothesis/history/{symbol}?limit=1')
        
        if not history_success or not history_data.get('records'):
            self.log_test("10. Price Tracking Feature", False, "Failed to get history for price tracking test")
            return False

        latest_record = history_data['records'][0]
        
        # Check price_at_creation field exists (can be null if no market data available)
        if 'price_at_creation' not in latest_record:
            self.log_test("10. Price Tracking Feature", False, "price_at_creation field missing from history")
            return False

        # If price is not null, verify it's a positive number
        price = latest_record['price_at_creation']
        if price is not None:
            if not isinstance(price, (int, float)) or price <= 0:
                self.log_test("10. Price Tracking Feature", False, f"Invalid price_at_creation value: {price}")
                return False

        self.log_test("10. Price Tracking Feature", True)
        return True

    def run_all_tests(self):
        """Run all PHASE 29.4 tests and print summary."""
        print("\n" + "=" * 80)
        print("PHASE 29.4 — Hypothesis Registry API Tests")
        print("=" * 80)
        print(f"Backend URL: {self.base_url}")
        print("-" * 80)
        
        # Run all tests
        test_methods = [
            self.test_hypothesis_current_with_storage,
            self.test_hypothesis_history_extended_fields,
            self.test_hypothesis_stats_endpoint,
            self.test_hypothesis_recent_endpoint,
            self.test_hypothesis_symbols_endpoint,
            self.test_hypothesis_recompute_with_storage,
            self.test_mongodb_persistence_fields,
            self.test_cross_symbol_statistics,
            self.test_recent_hypotheses_sorting,
            self.test_price_tracking_feature,
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(test_method.__name__, False, f"Exception: {str(e)}")
        
        # Print summary
        print("-" * 80)
        print(f"PHASE 29.4 Tests completed: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All PHASE 29.4 API tests passed!")
            return True
        else:
            failed_count = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_count} PHASE 29.4 API tests failed")
            return False


def main():
    """Run the PHASE 29.4 test suite."""
    tester = HypothesisRegistryAPITester()
    success = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())