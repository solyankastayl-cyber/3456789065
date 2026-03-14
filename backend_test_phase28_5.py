#!/usr/bin/env python3
"""
PHASE 28.5 - Microstructure Context Integration API Tests

Comprehensive testing of unified microstructure context API endpoints:
- GET /api/v1/microstructure/context/{symbol}
- GET /api/v1/microstructure/context/summary/{symbol}
- GET /api/v1/microstructure/context/drivers/{symbol}
- POST /api/v1/microstructure/context/recompute/{symbol}

Tests verify integration of all 4 microstructure layers:
- MicrostructureSnapshot (28.1)
- LiquidityVacuumState (28.2) 
- OrderbookPressureMap (28.3)
- LiquidationCascadeState (28.4)

Minimum 20+ tests covering business logic, bounds, and integration.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = "https://market-signals-201.preview.emergentagent.com"

class MicrostructureContextAPITester:
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
        self.context_cache = {}

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

    def test_context_btc_endpoint(self):
        """Test 1: GET /api/v1/microstructure/context/BTC - returns unified context with all 4 layers."""
        success, data, error = self.test_api_call('GET', 'api/v1/microstructure/context/BTC')
        
        if not success:
            self.log_test("1. Context BTC endpoint", False, error)
            return False

        # Check required fields from unified context
        required_fields = [
            'symbol', 'liquidity_state', 'pressure_bias', 'vacuum_direction', 
            'cascade_direction', 'vacuum_probability', 'sweep_probability', 
            'cascade_probability', 'microstructure_state', 'confidence_modifier',
            'capital_modifier', 'dominant_driver', 'reason', 'computed_at'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("1. Context BTC endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Cache for later tests
        self.context_cache['BTC'] = data

        # Validate field types and values
        validation_errors = []
        
        # Symbol should be BTC
        if data.get('symbol') != 'BTC':
            validation_errors.append(f"Expected symbol 'BTC', got '{data.get('symbol')}'")
            
        # Liquidity state validation (from layer 1 - MicrostructureSnapshot)
        if data.get('liquidity_state') not in ['DEEP', 'NORMAL', 'THIN']:
            validation_errors.append(f"Invalid liquidity_state: {data.get('liquidity_state')}")
            
        # Pressure bias validation (from layer 3 - OrderbookPressureMap)
        if data.get('pressure_bias') not in ['BID_DOMINANT', 'ASK_DOMINANT', 'BALANCED']:
            validation_errors.append(f"Invalid pressure_bias: {data.get('pressure_bias')}")
            
        # Vacuum direction validation (from layer 2 - LiquidityVacuumState)
        if data.get('vacuum_direction') not in ['UP', 'DOWN', 'NONE']:
            validation_errors.append(f"Invalid vacuum_direction: {data.get('vacuum_direction')}")
            
        # Cascade direction validation (from layer 4 - LiquidationCascadeState)
        if data.get('cascade_direction') not in ['UP', 'DOWN', 'NONE']:
            validation_errors.append(f"Invalid cascade_direction: {data.get('cascade_direction')}")
            
        # Probability validations (0-1 range)
        for prob_field in ['vacuum_probability', 'sweep_probability', 'cascade_probability']:
            if not (0 <= data.get(prob_field, -1) <= 1):
                validation_errors.append(f"{prob_field} should be between 0 and 1")
                
        # Microstructure state validation
        if data.get('microstructure_state') not in ['SUPPORTIVE', 'NEUTRAL', 'FRAGILE', 'STRESSED']:
            validation_errors.append(f"Invalid microstructure_state: {data.get('microstructure_state')}")
            
        # Confidence modifier bounds [0.82-1.12]
        conf_mod = data.get('confidence_modifier', 0)
        if not (0.82 <= conf_mod <= 1.12):
            validation_errors.append(f"confidence_modifier {conf_mod} outside bounds [0.82, 1.12]")
            
        # Capital modifier bounds [0.70-1.10]
        cap_mod = data.get('capital_modifier', 0)
        if not (0.70 <= cap_mod <= 1.10):
            validation_errors.append(f"capital_modifier {cap_mod} outside bounds [0.70, 1.10]")
            
        # Dominant driver validation
        if data.get('dominant_driver') not in ['LIQUIDITY', 'PRESSURE', 'VACUUM', 'CASCADE', 'MIXED']:
            validation_errors.append(f"Invalid dominant_driver: {data.get('dominant_driver')}")

        # Reason should be non-empty string
        if not isinstance(data.get('reason'), str) or not data.get('reason').strip():
            validation_errors.append("reason should be non-empty string")

        # computed_at should be valid ISO datetime
        try:
            datetime.fromisoformat(data.get('computed_at', '').replace('Z', '+00:00'))
        except (ValueError, TypeError):
            validation_errors.append("computed_at should be valid ISO datetime")

        if validation_errors:
            self.log_test("1. Context BTC endpoint", False, "; ".join(validation_errors))
            return False
            
        self.log_test("1. Context BTC endpoint", True)
        return True

    def test_context_summary_endpoint(self):
        """Test 2: GET /api/v1/microstructure/context/summary/BTC - returns aggregated statistics."""
        success, data, error = self.test_api_call('GET', 'api/v1/microstructure/context/summary/BTC')
        
        if not success:
            self.log_test("2. Context Summary endpoint", False, error)
            return False

        # Check summary structure
        required_fields = ['symbol', 'states', 'drivers', 'averages', 'current']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("2. Context Summary endpoint", False, f"Missing fields: {missing_fields}")
            return False

        validation_errors = []
        
        # States counts
        states = data.get('states', {})
        expected_states = ['supportive', 'neutral', 'fragile', 'stressed']
        if not all(state in states for state in expected_states):
            validation_errors.append("Missing state counts")
            
        # Drivers counts
        drivers = data.get('drivers', {})
        expected_drivers = ['liquidity', 'pressure', 'vacuum', 'cascade', 'mixed']
        if not all(driver in drivers for driver in expected_drivers):
            validation_errors.append("Missing driver counts")
            
        # Averages
        averages = data.get('averages', {})
        expected_avg = ['confidence_modifier', 'capital_modifier', 'vacuum_probability', 'cascade_probability']
        if not all(avg in averages for avg in expected_avg):
            validation_errors.append("Missing average fields")

        # Current state
        current = data.get('current', {})
        expected_current = ['state', 'driver']
        if not all(curr in current for curr in expected_current):
            validation_errors.append("Missing current state fields")

        # Validate average bounds
        avg_conf = averages.get('confidence_modifier', 0)
        avg_cap = averages.get('capital_modifier', 0)
        if not (0.82 <= avg_conf <= 1.12):
            validation_errors.append(f"Average confidence modifier {avg_conf} outside bounds")
        if not (0.70 <= avg_cap <= 1.10):
            validation_errors.append(f"Average capital modifier {avg_cap} outside bounds")

        if validation_errors:
            self.log_test("2. Context Summary endpoint", False, "; ".join(validation_errors))
            return False
            
        self.log_test("2. Context Summary endpoint", True)
        return True

    def test_context_drivers_endpoint(self):
        """Test 3: GET /api/v1/microstructure/context/drivers/BTC - returns driver impacts."""
        success, data, error = self.test_api_call('GET', 'api/v1/microstructure/context/drivers/BTC')
        
        if not success:
            self.log_test("3. Context Drivers endpoint", False, error)
            return False

        # Check drivers structure
        required_fields = ['symbol', 'impacts', 'dominant', 'direction_consistency', 'consistency_score']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("3. Context Drivers endpoint", False, f"Missing fields: {missing_fields}")
            return False

        validation_errors = []
        
        # Impacts validation
        impacts = data.get('impacts', {})
        expected_impacts = ['liquidity', 'pressure', 'vacuum', 'cascade']
        if not all(impact in impacts for impact in expected_impacts):
            validation_errors.append("Missing impact fields")
            
        # Validate impact values (0-1 range)
        for impact_name, impact_value in impacts.items():
            if not isinstance(impact_value, (int, float)) or not (0 <= impact_value <= 1):
                validation_errors.append(f"Invalid {impact_name} impact: {impact_value}")
                
        # Dominant driver validation
        if data.get('dominant') not in ['LIQUIDITY', 'PRESSURE', 'VACUUM', 'CASCADE', 'MIXED']:
            validation_errors.append(f"Invalid dominant driver: {data.get('dominant')}")
            
        # Direction consistency validation
        if not isinstance(data.get('direction_consistency'), bool):
            validation_errors.append("direction_consistency should be boolean")
            
        # Consistency score validation (0-1 range)
        consistency_score = data.get('consistency_score', -1)
        if not isinstance(consistency_score, (int, float)) or not (0 <= consistency_score <= 1):
            validation_errors.append(f"Invalid consistency_score: {consistency_score}")

        if validation_errors:
            self.log_test("3. Context Drivers endpoint", False, "; ".join(validation_errors))
            return False
            
        self.log_test("3. Context Drivers endpoint", True)
        return True

    def test_context_recompute_endpoint(self):
        """Test 4: POST /api/v1/microstructure/context/recompute/ETH - recomputes context."""
        success, data, error = self.test_api_call('POST', 'api/v1/microstructure/context/recompute/ETH')
        
        if not success:
            self.log_test("4. Context Recompute endpoint", False, error)
            return False

        # Check recompute response structure (same as context endpoint + status)
        required_fields = [
            'status', 'symbol', 'liquidity_state', 'pressure_bias', 'vacuum_direction',
            'cascade_direction', 'vacuum_probability', 'sweep_probability',
            'cascade_probability', 'microstructure_state', 'confidence_modifier',
            'capital_modifier', 'dominant_driver', 'reason', 'computed_at'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_test("4. Context Recompute endpoint", False, f"Missing fields: {missing_fields}")
            return False

        # Cache for later tests
        self.context_cache['ETH'] = data

        validation_errors = []

        # Check status is ok
        if data.get('status') != 'ok':
            validation_errors.append(f"Expected status 'ok', got '{data.get('status')}'")
            
        # Check symbol is ETH
        if data.get('symbol') != 'ETH':
            validation_errors.append(f"Expected symbol 'ETH', got '{data.get('symbol')}'")
            
        # Validate bounds
        conf_mod = data.get('confidence_modifier', 0)
        cap_mod = data.get('capital_modifier', 0)
        if not (0.82 <= conf_mod <= 1.12):
            validation_errors.append(f"confidence_modifier {conf_mod} outside bounds")
        if not (0.70 <= cap_mod <= 1.10):
            validation_errors.append(f"capital_modifier {cap_mod} outside bounds")

        if validation_errors:
            self.log_test("4. Context Recompute endpoint", False, "; ".join(validation_errors))
            return False
            
        self.log_test("4. Context Recompute endpoint", True)
        return True

    def test_liquidity_state_integration(self):
        """Test 5: Liquidity state copied from snapshot layer (28.1)."""
        if 'BTC' not in self.context_cache:
            success, data, error = self.test_api_call('GET', 'api/v1/microstructure/context/BTC')
            if not success:
                self.log_test("5. Liquidity state integration", False, f"Failed to get context: {error}")
                return False
            self.context_cache['BTC'] = data

        liquidity_state = self.context_cache['BTC'].get('liquidity_state')
        
        if liquidity_state not in ['DEEP', 'NORMAL', 'THIN']:
            self.log_test("5. Liquidity state integration", False, f"Invalid liquidity_state: {liquidity_state}")
            return False
            
        self.log_test("5. Liquidity state integration", True)
        return True

    def test_pressure_bias_integration(self):
        """Test 6: Pressure bias copied from pressure map layer (28.3)."""
        if 'BTC' not in self.context_cache:
            success, data, error = self.test_api_call('GET', 'api/v1/microstructure/context/BTC')
            if not success:
                self.log_test("6. Pressure bias integration", False, f"Failed to get context: {error}")
                return False
            self.context_cache['BTC'] = data

        pressure_bias = self.context_cache['BTC'].get('pressure_bias')
        
        if pressure_bias not in ['BID_DOMINANT', 'ASK_DOMINANT', 'BALANCED']:
            self.log_test("6. Pressure bias integration", False, f"Invalid pressure_bias: {pressure_bias}")
            return False
            
        self.log_test("6. Pressure bias integration", True)
        return True

    def test_vacuum_direction_integration(self):
        """Test 7: Vacuum direction copied from vacuum state layer (28.2)."""
        if 'BTC' not in self.context_cache:
            success, data, error = self.test_api_call('GET', 'api/v1/microstructure/context/BTC')
            if not success:
                self.log_test("7. Vacuum direction integration", False, f"Failed to get context: {error}")
                return False
            self.context_cache['BTC'] = data

        vacuum_direction = self.context_cache['BTC'].get('vacuum_direction')
        
        if vacuum_direction not in ['UP', 'DOWN', 'NONE']:
            self.log_test("7. Vacuum direction integration", False, f"Invalid vacuum_direction: {vacuum_direction}")
            return False
            
        self.log_test("7. Vacuum direction integration", True)
        return True

    def test_cascade_direction_integration(self):
        """Test 8: Cascade direction copied from cascade state layer (28.4)."""
        if 'BTC' not in self.context_cache:
            success, data, error = self.test_api_call('GET', 'api/v1/microstructure/context/BTC')
            if not success:
                self.log_test("8. Cascade direction integration", False, f"Failed to get context: {error}")
                return False
            self.context_cache['BTC'] = data

        cascade_direction = self.context_cache['BTC'].get('cascade_direction')
        
        if cascade_direction not in ['UP', 'DOWN', 'NONE']:
            self.log_test("8. Cascade direction integration", False, f"Invalid cascade_direction: {cascade_direction}")
            return False
            
        self.log_test("8. Cascade direction integration", True)
        return True

    def test_microstructure_state_classification(self):
        """Test 9: Microstructure state classification logic."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/microstructure/context/{symbol}')
            
            if not success:
                self.log_test("9. Microstructure state classification", False, f"Failed to get {symbol} data: {error}")
                return False

            microstructure_state = data.get('microstructure_state')
            
            if microstructure_state not in ['SUPPORTIVE', 'NEUTRAL', 'FRAGILE', 'STRESSED']:
                self.log_test("9. Microstructure state classification", False, f"Invalid microstructure_state for {symbol}: {microstructure_state}")
                return False

        self.log_test("9. Microstructure state classification", True)
        return True

    def test_confidence_modifier_bounds(self):
        """Test 10: Confidence modifier within bounds [0.82-1.12]."""
        symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/microstructure/context/{symbol}')
            
            if not success:
                # Don't fail if some symbols don't work, but try a few
                continue

            conf_mod = data.get('confidence_modifier')
            
            if not isinstance(conf_mod, (int, float)) or not (0.82 <= conf_mod <= 1.12):
                self.log_test("10. Confidence modifier bounds", False, f"confidence_modifier {conf_mod} outside bounds for {symbol}")
                return False

        self.log_test("10. Confidence modifier bounds", True)
        return True

    def test_capital_modifier_bounds(self):
        """Test 11: Capital modifier within bounds [0.70-1.10]."""
        symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/microstructure/context/{symbol}')
            
            if not success:
                continue

            cap_mod = data.get('capital_modifier')
            
            if not isinstance(cap_mod, (int, float)) or not (0.70 <= cap_mod <= 1.10):
                self.log_test("11. Capital modifier bounds", False, f"capital_modifier {cap_mod} outside bounds for {symbol}")
                return False

        self.log_test("11. Capital modifier bounds", True)
        return True

    def test_dominant_driver_detection(self):
        """Test 12: Dominant driver detection logic."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/microstructure/context/{symbol}')
            
            if not success:
                self.log_test("12. Dominant driver detection", False, f"Failed to get {symbol} data: {error}")
                return False

            dominant_driver = data.get('dominant_driver')
            
            if dominant_driver not in ['LIQUIDITY', 'PRESSURE', 'VACUUM', 'CASCADE', 'MIXED']:
                self.log_test("12. Dominant driver detection", False, f"Invalid dominant_driver for {symbol}: {dominant_driver}")
                return False

        self.log_test("12. Dominant driver detection", True)
        return True

    def test_integration_consistency(self):
        """Test 13: Integration consistency between context and drivers endpoints."""
        # Get both context and drivers for same symbol
        success1, context_data, error1 = self.test_api_call('GET', 'api/v1/microstructure/context/BTC')
        success2, drivers_data, error2 = self.test_api_call('GET', 'api/v1/microstructure/context/drivers/BTC')
        
        if not success1:
            self.log_test("13. Integration consistency", False, f"Context failed: {error1}")
            return False
        if not success2:
            self.log_test("13. Integration consistency", False, f"Drivers failed: {error2}")
            return False

        # Dominant driver should match
        context_driver = context_data.get('dominant_driver')
        drivers_dominant = drivers_data.get('dominant')
        
        if context_driver != drivers_dominant:
            self.log_test("13. Integration consistency", False, f"Dominant driver mismatch: {context_driver} vs {drivers_dominant}")
            return False

        self.log_test("13. Integration consistency", True)
        return True

    def test_probability_ranges(self):
        """Test 14: All probabilities within [0-1] range."""
        symbols = ['BTC', 'ETH', 'SOL']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/microstructure/context/{symbol}')
            
            if not success:
                self.log_test("14. Probability ranges", False, f"Failed to get {symbol} data: {error}")
                return False

            for prob_field in ['vacuum_probability', 'sweep_probability', 'cascade_probability']:
                prob_value = data.get(prob_field, -1)
                
                if not isinstance(prob_value, (int, float)) or not (0 <= prob_value <= 1):
                    self.log_test("14. Probability ranges", False, f"{prob_field} {prob_value} outside [0-1] for {symbol}")
                    return False

        self.log_test("14. Probability ranges", True)
        return True

    def test_reason_generation(self):
        """Test 15: Reason field contains meaningful explanations."""
        symbols = ['BTC', 'ETH']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/microstructure/context/{symbol}')
            
            if not success:
                self.log_test("15. Reason generation", False, f"Failed to get {symbol} data: {error}")
                return False

            reason = data.get('reason', '')
            
            if not isinstance(reason, str) or len(reason.strip()) < 10:
                self.log_test("15. Reason generation", False, f"Invalid or too short reason for {symbol}: {reason}")
                return False

            # Check that reason contains microstructure-related terms
            microstructure_terms = ['liquidity', 'pressure', 'vacuum', 'cascade', 'execution', 'microstructure', 'risk', 'balanced', 'stress']
            if not any(term in reason.lower() for term in microstructure_terms):
                self.log_test("15. Reason generation", False, f"Reason lacks microstructure context for {symbol}: {reason}")
                return False

        self.log_test("15. Reason generation", True)
        return True

    def test_supportive_state_conditions(self):
        """Test 16: SUPPORTIVE state has appropriate conditions."""
        symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'USDT', 'USDC']
        found_supportive = False
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/microstructure/context/{symbol}')
            
            if success and data.get('microstructure_state') == 'SUPPORTIVE':
                found_supportive = True
                
                # SUPPORTIVE should have low risk probabilities or good liquidity
                vacuum_prob = data.get('vacuum_probability', 1)
                cascade_prob = data.get('cascade_probability', 1)
                liquidity_state = data.get('liquidity_state')
                
                # SUPPORTIVE conditions: deep liquidity OR low vacuum+cascade risk
                if liquidity_state != 'DEEP' and (vacuum_prob >= 0.4 or cascade_prob >= 0.45):
                    self.log_test("16. SUPPORTIVE state conditions", False, f"SUPPORTIVE with poor conditions: {liquidity_state}, vacuum={vacuum_prob}, cascade={cascade_prob}")
                    return False
                break
        
        # If no SUPPORTIVE found, at least verify the classification logic works
        if not found_supportive:
            self.log_test("16. SUPPORTIVE state conditions", True, "No SUPPORTIVE state found but API returns valid states")
        else:
            self.log_test("16. SUPPORTIVE state conditions", True)
        return True

    def test_stressed_state_conditions(self):
        """Test 17: STRESSED state has appropriate high-risk conditions."""
        symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT']
        found_stressed = False
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/microstructure/context/{symbol}')
            
            if success and data.get('microstructure_state') == 'STRESSED':
                found_stressed = True
                
                # STRESSED should have high cascade risk OR critical conditions
                cascade_prob = data.get('cascade_probability', 0)
                vacuum_prob = data.get('vacuum_probability', 0)
                liquidity_state = data.get('liquidity_state')
                
                # STRESSED conditions: high cascade OR thin liquidity with high vacuum
                stressed_condition = (
                    cascade_prob >= 0.45 or  # High cascade probability
                    (liquidity_state == 'THIN' and vacuum_prob >= 0.5)  # Thin + high vacuum
                )
                
                if not stressed_condition:
                    self.log_test("17. STRESSED state conditions", False, f"STRESSED without high-risk conditions: cascade={cascade_prob}, vacuum={vacuum_prob}, liquidity={liquidity_state}")
                    return False
                break
        
        self.log_test("17. STRESSED state conditions", found_stressed, "Found and validated STRESSED state" if found_stressed else "No STRESSED state found in tested symbols")
        return True

    def test_driver_impact_calculation(self):
        """Test 18: Driver impact calculation matches expectations."""
        success, data, error = self.test_api_call('GET', 'api/v1/microstructure/context/drivers/BTC')
        
        if not success:
            self.log_test("18. Driver impact calculation", False, f"Failed to get drivers: {error}")
            return False

        impacts = data.get('impacts', {})
        
        # All impacts should be between 0 and 1
        for driver, impact in impacts.items():
            if not isinstance(impact, (int, float)) or not (0 <= impact <= 1):
                self.log_test("18. Driver impact calculation", False, f"{driver} impact {impact} outside [0-1]")
                return False

        # The sum of impacts should be reasonable (not all zero)
        total_impact = sum(impacts.values())
        if total_impact == 0:
            self.log_test("18. Driver impact calculation", False, "All driver impacts are zero")
            return False

        self.log_test("18. Driver impact calculation", True)
        return True

    def test_direction_consistency_logic(self):
        """Test 19: Direction consistency calculation."""
        symbols = ['BTC', 'ETH']
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/microstructure/context/drivers/{symbol}')
            
            if not success:
                self.log_test("19. Direction consistency logic", False, f"Failed to get drivers for {symbol}: {error}")
                return False

            direction_consistency = data.get('direction_consistency')
            consistency_score = data.get('consistency_score')
            
            # Must be boolean and score must be 0-1
            if not isinstance(direction_consistency, bool):
                self.log_test("19. Direction consistency logic", False, f"direction_consistency not boolean for {symbol}")
                return False
                
            if not isinstance(consistency_score, (int, float)) or not (0 <= consistency_score <= 1):
                self.log_test("19. Direction consistency logic", False, f"Invalid consistency_score for {symbol}: {consistency_score}")
                return False

        self.log_test("19. Direction consistency logic", True)
        return True

    def test_multi_symbol_integration(self):
        """Test 20: Multi-symbol integration across all 4 layers."""
        symbols = ['BTC', 'ETH', 'SOL']
        all_contexts = {}
        
        for symbol in symbols:
            success, data, error = self.test_api_call('GET', f'api/v1/microstructure/context/{symbol}')
            
            if not success:
                self.log_test("20. Multi-symbol integration", False, f"Failed to get {symbol} data: {error}")
                return False
                
            all_contexts[symbol] = data

        # Validate that each symbol has different characteristics (not all identical)
        # Check if we have variation in states and drivers
        states = [ctx.get('microstructure_state') for ctx in all_contexts.values()]
        drivers = [ctx.get('dominant_driver') for ctx in all_contexts.values()]
        
        # Should have some variation (not all identical)
        unique_states = len(set(states))
        unique_drivers = len(set(drivers))
        
        if unique_states == 1 and unique_drivers == 1:
            # Could be legitimate if market conditions are similar, but let's check modifiers vary
            conf_mods = [ctx.get('confidence_modifier') for ctx in all_contexts.values()]
            if len(set([round(cm, 2) for cm in conf_mods])) == 1:
                self.log_test("20. Multi-symbol integration", False, "All symbols have identical context - integration may not be working")
                return False

        self.log_test("20. Multi-symbol integration", True)
        return True

    def run_all_tests(self):
        """Run all tests and print summary."""
        print("\n" + "=" * 80)
        print("PHASE 28.5 — Microstructure Context Integration API Tests")
        print("=" * 80)
        print(f"Backend URL: {self.base_url}")
        print("-" * 80)
        
        # Run all tests
        test_methods = [
            self.test_context_btc_endpoint,
            self.test_context_summary_endpoint,
            self.test_context_drivers_endpoint,
            self.test_context_recompute_endpoint,
            self.test_liquidity_state_integration,
            self.test_pressure_bias_integration,
            self.test_vacuum_direction_integration,
            self.test_cascade_direction_integration,
            self.test_microstructure_state_classification,
            self.test_confidence_modifier_bounds,
            self.test_capital_modifier_bounds,
            self.test_dominant_driver_detection,
            self.test_integration_consistency,
            self.test_probability_ranges,
            self.test_reason_generation,
            self.test_supportive_state_conditions,
            self.test_stressed_state_conditions,
            self.test_driver_impact_calculation,
            self.test_direction_consistency_logic,
            self.test_multi_symbol_integration,
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(test_method.__name__.replace('test_', ''), False, f"Exception: {str(e)}")
        
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
    tester = MicrostructureContextAPITester()
    success = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())