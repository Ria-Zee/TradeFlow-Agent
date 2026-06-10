import sys
import os
import pytest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import ConfidenceLevel, TradeRecommendation
from core.tools import get_fx_rate, get_trade_context
from tradeflow import run_tradeflow

def test_fx_api():
    print("TEST 1: Live FX API")
    result = get_fx_rate("USD", "NGN")
    if result["status"] != "LIVE":
        pytest.skip(f"Live FX API unavailable in this environment: {result.get('error')}")
    assert result["rate"] > 0, "Invalid FX rate"
    print(f"  PASSED: USD/NGN = {result['rate']}")

def test_scenario_smartphones():
    print("\nTEST 2: Smartphone Import Scenario")
    brief = run_tradeflow(
        raw_query="I want to import 500 units of Samsung smartphones from China to Lagos.",
        product="Samsung smartphones",
        quantity=500,
        origin="China",
        destination_port="apapa",
        disruption_type=None
    )
    assert brief.market_intel is not None, "Market Intel agent failed"
    assert brief.route_logistics is not None, "Route Logistics agent failed"
    assert brief.risk_compliance is not None, "Risk Compliance agent failed"
    assert brief.critic_verdict is not None, "Critic agent failed"
    assert brief.final_recommendation in list(TradeRecommendation), "Invalid recommendation"
    if brief.live_data.usd_ngn_rate is None:
        assert "FX_UNAVAILABLE" in brief.live_data.data_quality
        print("  PASSED: Live FX unavailable; fallback analysis completed")
    else:
        print(f"  PASSED: Live USD/NGN = {brief.live_data.usd_ngn_rate}")
    print(f"  PASSED: Recommendation = {brief.final_recommendation}")

def test_scenario_solar_panels():
    print("\nTEST 3: Solar Panel Import Scenario")
    brief = run_tradeflow(
        raw_query="I want to import 200 units of solar inverters from China to Lagos via Cotonou.",
        product="solar inverters",
        quantity=200,
        origin="China",
        destination_port="cotonou",
        disruption_type=None
    )
    assert brief.market_intel is not None, "Market Intel agent failed"
    assert brief.critic_verdict is not None, "Critic agent failed"
    assert brief.final_recommendation in list(TradeRecommendation), "Invalid recommendation"
    print(f"  PASSED: Recommendation = {brief.final_recommendation}")

def test_disruption_loop():
    print("\nTEST 4: Crisis Commander Disruption Loop")
    brief = run_tradeflow(
        raw_query="I want to import 100 units of laptops from China to Lagos.",
        product="laptops",
        quantity=100,
        origin="China",
        destination_port="apapa",
        disruption_type="port_closure"
    )
    assert brief is not None, "Disruption loop failed"
    assert brief.critic_verdict is not None, "Post-disruption analysis failed"
    print(f"  PASSED: Post-disruption recommendation = {brief.final_recommendation}")

if __name__ == "__main__":
    print("="*60)
    print("TRADEFLOW TEST SUITE")
    print("="*60)
    passed = 0
    failed = 0
    tests = [test_fx_api, test_scenario_smartphones, test_scenario_solar_panels, test_disruption_loop]
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
