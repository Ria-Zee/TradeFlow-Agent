import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import TradeQuery, TradeBrief, LiveDataContext, TradeRecommendation
from core.tools import get_trade_context, check_disruption_signals
from agents import market_intel, route_logistics, risk_compliance, critic

DISRUPTIONS = {
    "port_closure": "DISRUPTION ALERT: Apapa port has been closed due to a labor strike. All cargo operations suspended indefinitely.",
    "fx_spike": "DISRUPTION ALERT: The Naira has devalued sharply. USD/NGN has spiked 15% in the last 24 hours due to CBN policy change.",
    "policy_change": "DISRUPTION ALERT: Nigerian Customs has issued an emergency directive imposing a new 30-day pre-shipment inspection requirement on all electronics imports.",
    "supplier_risk": "DISRUPTION ALERT: A major fraud alert has been issued for electronics suppliers in Shenzhen. Several Nigerian importers have reported receiving counterfeit goods.",
}

def fetch_live_data(product: str, origin: str, destination: str) -> tuple:
    print("  Fetching live market intelligence...")
    context = get_trade_context(product, origin, destination)
    fx = context["fx_rates"]
    shipping = context["shipping_estimate"]
    news = context["trade_news"]
    disruptions = context["disruption_monitor"]

    live_data = LiveDataContext(
        usd_ngn_rate=fx["USD_NGN"].get("rate"),
        usd_cny_rate=fx["USD_CNY"].get("rate"),
        cny_ngn_rate=fx["CNY_NGN"].get("rate"),
        shipping_min=shipping.get("freight_usd_min"),
        shipping_max=shipping.get("freight_usd_max"),
        shipping_transit_days=shipping.get("transit_days"),
        data_timestamp=context["data_timestamp"],
        data_quality=context["data_quality"]
    )
    return live_data, news, disruptions

def print_trace(agent_output, step: int, total: int):
    print(f"\n--- REASONING TRACE: {agent_output.agent_name} [{step}/{total}] ---")
    print(f"Confidence: {agent_output.confidence}")
    if agent_output.assumptions:
        for a in agent_output.assumptions[:2]:
            print(f"  * {a}")
    print(f"Flags: {', '.join(agent_output.flags)}")
    print(f"Preview: {agent_output.analysis[:180]}...")
    print("-"*60)

def run_agent_chain(query: TradeQuery, live_data: LiveDataContext) -> TradeBrief:
    brief = TradeBrief(query=query, live_data=live_data)

    print("  [1/4] Market Intelligence Agent (Foundry IQ + Live FX + Live News)...")
    brief.market_intel = market_intel.run(query, live_data)
    print_trace(brief.market_intel, 1, 4)

    print("  [2/4] Route and Logistics Agent (Foundry IQ)...")
    brief.route_logistics = route_logistics.run(query, live_data, brief.market_intel.analysis)
    print_trace(brief.route_logistics, 2, 4)

    print("  [3/4] Risk and Compliance Agent (Foundry IQ)...")
    brief.risk_compliance = risk_compliance.run(query, live_data, brief.market_intel.analysis, brief.route_logistics.analysis)
    print_trace(brief.risk_compliance, 3, 4)

    print("  [4/4] Critic and Verifier Agent (Disagreement Detection + Confidence Ledger)...")
    result = critic.run(query, live_data, brief.market_intel, brief.route_logistics, brief.risk_compliance)
    brief.critic_verdict, brief.final_recommendation, brief.final_verdict, brief.agent_disagreements, brief.confidence_ledger = result
    print_trace(brief.critic_verdict, 4, 4)

    return brief

def print_brief(brief: TradeBrief, label: str):
    print("\n" + "="*60)
    print(f"TRADE DECISION BRIEF: {label}")
    print("="*60)
    print(brief.critic_verdict.analysis)
    if brief.final_verdict:
        print(f"\nFINAL VERDICT: {brief.final_verdict}")
    print("="*60)

def print_news_intelligence(news: dict, disruptions: dict):
    print("\n" + "="*60)
    print("LIVE TRADE INTELLIGENCE FEED")
    print("="*60)
    print(f"Disruption Risk Level: {disruptions.get('risk_level', 'UNKNOWN')}")
    signals = disruptions.get("disruption_signals", [])
    if signals:
        print("ACTIVE DISRUPTION SIGNALS:")
        for s in signals:
            print(f"  ! {s}")
    else:
        print("No active disruption signals detected.")
    print(f"\nLive Nigerian Trade Headlines:")
    for a in news.get("articles", [])[:5]:
        print(f"  → {a['title'][:100]}")
    print("="*60)

def print_traceability_report(initial_brief: TradeBrief, revised_brief: TradeBrief = None):
    print("\n" + "="*60)
    print("DECISION TRACEABILITY REPORT")
    print("="*60)
    print(f"Live USD/NGN: {initial_brief.live_data.usd_ngn_rate} (LIVE)")
    print(f"Live USD/CNY: {initial_brief.live_data.usd_cny_rate} (LIVE)")
    print(f"Shipping Estimate: USD {initial_brief.live_data.shipping_min}-{initial_brief.live_data.shipping_max} (ESTIMATED)")
    print(f"Data Quality: {initial_brief.live_data.data_quality}")
    print(f"Timestamp: {initial_brief.live_data.data_timestamp}")
    print(f"\nAgent Chain: Market Intel → Route Logistics → Risk Compliance → Critic")
    print(f"\nCONFIDENCE SCORES:")
    print(f"  Market Intel:    {initial_brief.market_intel.confidence}")
    print(f"  Route Logistics: {initial_brief.route_logistics.confidence}")
    print(f"  Risk Compliance: {initial_brief.risk_compliance.confidence}")
    print(f"  Final Verdict:   {initial_brief.critic_verdict.confidence}")
    if initial_brief.confidence_ledger:
        score = initial_brief.confidence_ledger.get('score', 'N/A')
        print(f"\nCONFIDENCE LEDGER: {score}/100")
        for r in initial_brief.confidence_ledger.get('raises_confidence', []):
            print(f"  + {r}")
        for l in initial_brief.confidence_ledger.get('lowers_confidence', []):
            print(f"  - {l}")
    if initial_brief.agent_disagreements:
        print(f"\nAGENT DISAGREEMENTS DETECTED:")
        for d in initial_brief.agent_disagreements:
            print(f"  ! {d}")
    print(f"\nFOUNDRY IQ: african-trade-knowledge index")
    all_flags = list(dict.fromkeys(
        initial_brief.market_intel.flags +
        initial_brief.route_logistics.flags +
        initial_brief.risk_compliance.flags +
        initial_brief.critic_verdict.flags
    ))
    print(f"SYSTEM FLAGS: {', '.join(all_flags)}")
    if revised_brief:
        print(f"\nDISRUPTION IMPACT:")
        print(f"  Before: {initial_brief.critic_verdict.confidence}")
        print(f"  After:  {revised_brief.critic_verdict.confidence}")
    print("="*60)

def run_scenario_comparison(raw_query: str, product: str, quantity: int,
                            origin: str, scenario_a_port: str, scenario_b_port: str):
    print("\n" + "="*60)
    print("TRADEFLOW SCENARIO COMPARISON ENGINE")
    print("="*60)
    print(f"Comparing: {scenario_a_port.upper()} vs {scenario_b_port.upper()}")
    print(f"Query: {raw_query}")
    print("="*60)

    print(f"\nAnalyzing Scenario A: {scenario_a_port.upper()}...")
    live_data_a, news_a, disruptions_a = fetch_live_data(product, origin, scenario_a_port)
    query_a = TradeQuery(raw=f"{raw_query} via {scenario_a_port}", product=product,
                         quantity=quantity, origin=origin, destination="Nigeria")
    brief_a = run_agent_chain(query_a, live_data_a)

    print(f"\nAnalyzing Scenario B: {scenario_b_port.upper()}...")
    live_data_b, news_b, disruptions_b = fetch_live_data(product, origin, scenario_b_port)
    query_b = TradeQuery(raw=f"{raw_query} via {scenario_b_port}", product=product,
                         quantity=quantity, origin=origin, destination="Nigeria")
    brief_b = run_agent_chain(query_b, live_data_b)

    print("\n" + "="*60)
    print("SCENARIO COMPARISON MATRIX")
    print("="*60)
    print(f"{'Dimension':<30} {''+scenario_a_port.upper():<25} {''+scenario_b_port.upper():<25}")
    print("-"*80)
    print(f"{'Recommendation':<30} {str(brief_a.final_recommendation.value):<25} {str(brief_b.final_recommendation.value):<25}")
    print(f"{'Market Intel Confidence':<30} {str(brief_a.market_intel.confidence.value):<25} {str(brief_b.market_intel.confidence.value):<25}")
    print(f"{'Logistics Confidence':<30} {str(brief_a.route_logistics.confidence.value):<25} {str(brief_b.route_logistics.confidence.value):<25}")
    print(f"{'Risk Confidence':<30} {str(brief_a.risk_compliance.confidence.value):<25} {str(brief_b.risk_compliance.confidence.value):<25}")
    print(f"{'Final Confidence':<30} {str(brief_a.critic_verdict.confidence.value):<25} {str(brief_b.critic_verdict.confidence.value):<25}")
    conf_a = brief_a.confidence_ledger.get('score', 0)
    conf_b = brief_b.confidence_ledger.get('score', 0)
    print(f"{'Confidence Score':<30} {str(conf_a)+'/100':<25} {str(conf_b)+'/100':<25}")
    print(f"{'Freight USD':<30} {str(live_data_a.shipping_min)+'-'+str(live_data_a.shipping_max):<25} {str(live_data_b.shipping_min)+'-'+str(live_data_b.shipping_max):<25}")
    print(f"{'Transit Days':<30} {str(live_data_a.shipping_transit_days):<25} {str(live_data_b.shipping_transit_days):<25}")
    print(f"{'Disruption Risk':<30} {disruptions_a.get('risk_level','N/A'):<25} {disruptions_b.get('risk_level','N/A'):<25}")
    print("-"*80)
    if conf_a >= conf_b:
        winner = scenario_a_port.upper()
        winner_score = conf_a
    else:
        winner = scenario_b_port.upper()
        winner_score = conf_b
    print(f"RECOMMENDED ROUTE: {winner} (Confidence Score: {winner_score}/100)")
    print("="*60)
    return brief_a, brief_b

def run_tradeflow(raw_query: str, product: str = "goods", quantity: int = 0,
                  origin: str = "China", destination_port: str = "apapa",
                  disruption_type: str = None, compare_port: str = None):

    print("\n" + "="*60)
    print("TRADEFLOW COMMAND SYSTEM")
    print("African Trade Intelligence Platform")
    print("Powered by Microsoft Azure AI Foundry + Foundry IQ")
    print("="*60)
    print(f"Query: {raw_query}")
    print("="*60)

    if compare_port:
        return run_scenario_comparison(raw_query, product, quantity, origin,
                                       destination_port, compare_port)

    live_data, news, disruptions = fetch_live_data(product, origin, destination_port)
    print(f"  Live USD/NGN: {live_data.usd_ngn_rate}")
    print(f"  Disruption Risk: {disruptions.get('risk_level')}")
    print(f"  News articles: {news.get('count', 0)}")

    print_news_intelligence(news, disruptions)

    auto_disruption = None
    if disruptions.get('risk_level') == 'HIGH' and not disruption_type:
        auto_disruption = disruptions.get('disruption_signals', [])
        print("\n" + "!"*60)
        print("PROACTIVE DISRUPTION ALERT - AUTO-DETECTED")
        print("!"*60)
        for signal in auto_disruption:
            print(f"  ! {signal}")
        print("!"*60)

    query = TradeQuery(
        raw=raw_query, product=product, quantity=quantity,
        origin=origin, destination="Nigeria"
    )

    print("\nPHASE 1: Initial Trade Intelligence Analysis")
    print("-"*60)
    initial_brief = run_agent_chain(query, live_data)
    print_brief(initial_brief, "INITIAL ASSESSMENT")

    revised_brief = None

    if disruption_type and disruption_type in DISRUPTIONS:
        disruption_message = DISRUPTIONS[disruption_type]
        print("\n" + "!"*60)
        print("DISRUPTION SIGNAL RECEIVED")
        print("!"*60)
        print(disruption_message)
        print("!"*60)
        print("\nPHASE 2: Re-analyzing with disruption context...")
        print("-"*60)

        disrupted_query = TradeQuery(
            raw=raw_query, product=product, quantity=quantity,
            origin=origin, destination="Nigeria",
            disruption_context=disruption_message
        )
        revised_live_data, _, _ = fetch_live_data(product, origin, destination_port)
        revised_brief = run_agent_chain(disrupted_query, revised_live_data)
        print_brief(revised_brief, "REVISED ASSESSMENT POST-DISRUPTION")

    print_traceability_report(initial_brief, revised_brief)
    return revised_brief if revised_brief else initial_brief

if __name__ == "__main__":
    run_tradeflow(
        raw_query="I want to import 500 units of Samsung smartphones from China to Lagos.",
        product="Samsung smartphones",
        quantity=500,
        origin="China",
        destination_port="apapa",
        disruption_type="port_closure",
        compare_port=None
    )
