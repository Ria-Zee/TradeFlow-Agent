import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import TradeQuery, TradeBrief, LiveDataContext
from core.tools import get_trade_context
from core.disagreement import analyze_disagreements, print_disagreement_report
from agents import market_intel, route_logistics, risk_compliance, critic

def fetch_live_data(product, origin, destination):
    context = get_trade_context(product, origin, destination)
    fx = context["fx_rates"]
    shipping = context["shipping_estimate"]
    return LiveDataContext(
        usd_ngn_rate=fx["USD_NGN"].get("rate"),
        usd_cny_rate=fx["USD_CNY"].get("rate"),
        cny_ngn_rate=fx["CNY_NGN"].get("rate"),
        shipping_min=shipping.get("freight_usd_min"),
        shipping_max=shipping.get("freight_usd_max"),
        shipping_transit_days=shipping.get("transit_days"),
        data_timestamp=context["data_timestamp"],
        data_quality=context["data_quality"]
    ), context["trade_news"], context["disruption_monitor"]

def run_single_chain(query, live_data):
    brief = TradeBrief(query=query, live_data=live_data)
    brief.market_intel = market_intel.run(query, live_data)
    brief.route_logistics = route_logistics.run(query, live_data, brief.market_intel.analysis)
    brief.risk_compliance = risk_compliance.run(query, live_data, brief.market_intel.analysis, brief.route_logistics.analysis)
    result = critic.run(query, live_data, brief.market_intel, brief.route_logistics, brief.risk_compliance)
    brief.critic_verdict, brief.final_recommendation, brief.final_verdict, brief.agent_disagreements, brief.confidence_ledger = result
    return brief

def run_scenario_comparison(raw_query, product, quantity, origin, port_a, port_b):
    print("\n" + "="*60)
    print("TRADEFLOW SCENARIO COMPARISON ENGINE")
    print("="*60)
    print(f"Scenario A: {port_a.upper()}  vs  Scenario B: {port_b.upper()}")
    print(f"Query: {raw_query}")
    print("="*60)

    print(f"\n[A] Analyzing {port_a.upper()}...")
    live_a, news_a, dis_a = fetch_live_data(product, origin, port_a)
    query_a = TradeQuery(raw=f"{raw_query} via {port_a}", product=product,
                         quantity=quantity, origin=origin, destination="Nigeria")
    brief_a = run_single_chain(query_a, live_a)
    disagree_a = analyze_disagreements(brief_a.market_intel, brief_a.route_logistics, brief_a.risk_compliance)

    print(f"\n[B] Analyzing {port_b.upper()}...")
    live_b, news_b, dis_b = fetch_live_data(product, origin, port_b)
    query_b = TradeQuery(raw=f"{raw_query} via {port_b}", product=product,
                         quantity=quantity, origin=origin, destination="Nigeria")
    brief_b = run_single_chain(query_b, live_b)
    disagree_b = analyze_disagreements(brief_b.market_intel, brief_b.route_logistics, brief_b.risk_compliance)

    conf_a = brief_a.confidence_ledger.get('score', 0) if brief_a.confidence_ledger else 0
    conf_b = brief_b.confidence_ledger.get('score', 0) if brief_b.confidence_ledger else 0

    print("\n" + "="*60)
    print("SCENARIO COMPARISON MATRIX")
    print("="*60)
    print(f"{'Dimension':<35} {port_a.upper():<22} {port_b.upper():<22}")
    print("-"*80)
    print(f"{'Recommendation':<35} {str(brief_a.final_recommendation.value):<22} {str(brief_b.final_recommendation.value):<22}")
    print(f"{'Final Confidence':<35} {str(brief_a.critic_verdict.confidence.value):<22} {str(brief_b.critic_verdict.confidence.value):<22}")
    print(f"{'Confidence Score':<35} {str(conf_a)+'/100':<22} {str(conf_b)+'/100':<22}")
    print(f"{'Freight USD (est)':<35} {str(live_a.shipping_min)+'-'+str(live_a.shipping_max):<22} {str(live_b.shipping_min)+'-'+str(live_b.shipping_max):<22}")
    print(f"{'Transit Days (est)':<35} {str(live_a.shipping_transit_days):<22} {str(live_b.shipping_transit_days):<22}")
    print(f"{'Disruption Risk':<35} {dis_a.get('risk_level','N/A'):<22} {dis_b.get('risk_level','N/A'):<22}")
    print(f"{'Agent Conflicts':<35} {str(disagree_a['disagreement_count'])+' detected':<22} {str(disagree_b['disagreement_count'])+' detected':<22}")
    print("-"*80)

    winner = port_a.upper() if conf_a >= conf_b else port_b.upper()
    winner_score = max(conf_a, conf_b)
    loser_score = min(conf_a, conf_b)
    print(f"\nRECOMMENDED ROUTE: {winner}")
    print(f"Confidence Score: {winner_score}/100 vs {loser_score}/100")
    if brief_a.final_verdict:
        print(f"\nScenario A Final Verdict: {brief_a.final_verdict}")
    if brief_b.final_verdict:
        print(f"Scenario B Final Verdict: {brief_b.final_verdict}")
    print("="*60)
    return brief_a, brief_b

if __name__ == "__main__":
    run_scenario_comparison(
        raw_query="I want to import 500 units of Samsung smartphones from China to Lagos",
        product="Samsung smartphones",
        quantity=500,
        origin="China",
        port_a="apapa",
        port_b="cotonou"
    )
