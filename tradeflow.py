import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import TradeQuery, TradeBrief, LiveDataContext, TradeRecommendation
from core.tools import get_trade_context, check_disruption_signals
from core.disagreement import analyze_disagreements, print_disagreement_report
from agents import market_intel, route_logistics, risk_compliance, critic

DISRUPTIONS = {
    "port_closure": "DISRUPTION ALERT: Apapa port has been closed due to a labor strike. All cargo operations suspended indefinitely.",
    "fx_spike": "DISRUPTION ALERT: The Naira has devalued sharply. USD/NGN has spiked 15% in the last 24 hours due to CBN policy change.",
    "policy_change": "DISRUPTION ALERT: Nigerian Customs has issued an emergency directive imposing a new 30-day pre-shipment inspection requirement on all electronics imports.",
    "supplier_risk": "DISRUPTION ALERT: A major fraud alert has been issued for electronics suppliers in Shenzhen. Several Nigerian importers have reported receiving counterfeit goods.",
}

WORKFLOW_TRACE = []

def trace(node: str, status: str, detail: str = ""):
    entry = f"  {'✔' if status == 'OK' else '⚠'} {node} → {detail}"
    WORKFLOW_TRACE.append(entry)
    print(entry)

def fetch_live_data(product, origin, destination):
    context = get_trade_context(product, origin, destination)
    fx = context["fx_rates"]
    shipping = context["shipping_estimate"]
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
    return live_data, context["trade_news"], context["disruption_monitor"]

def run_agent_chain(query: TradeQuery, live_data: LiveDataContext) -> TradeBrief:
    global WORKFLOW_TRACE
    WORKFLOW_TRACE = []
    brief = TradeBrief(query=query, live_data=live_data)

    print("\n" + "-"*60)
    print("WORKFLOW EXECUTION TRACE")
    print("-"*60)
    trace("Orchestrator Node", "OK", "query parsed and decomposed into specialist tasks")

    print("  [Specialist Execution Layer — passing each agent the context it needs]")
    brief.market_intel = market_intel.run(query, live_data)
    brief.route_logistics = route_logistics.run(query, live_data, brief.market_intel.analysis)
    brief.risk_compliance = risk_compliance.run(query, live_data, brief.market_intel.analysis, brief.route_logistics.analysis)

    trace("Market Intelligence Node", "OK",
          f"economic viability assessed | confidence: {brief.market_intel.confidence} | flags: {', '.join(brief.market_intel.flags)}")
    trace("Route & Logistics Node", "OK",
          f"routing strategy determined | confidence: {brief.route_logistics.confidence}")
    trace("Risk & Compliance Node", "OK",
          f"regulatory risks identified | confidence: {brief.risk_compliance.confidence}")

    trace("Aggregation Node", "OK", "specialist outputs merged into unified trade brief")

    disagreement_analysis = analyze_disagreements(brief.market_intel, brief.route_logistics, brief.risk_compliance)
    if disagreement_analysis['disagreement_count'] > 0:
        trace("Disagreement Detector", "⚠",
              f"{disagreement_analysis['disagreement_count']} contradiction(s) detected — confidence adjustment required")
    else:
        trace("Disagreement Detector", "OK", "agents in agreement — no contradictions found")

    result = critic.run(query, live_data, brief.market_intel, brief.route_logistics, brief.risk_compliance)
    brief.critic_verdict, brief.final_recommendation, brief.final_verdict, brief.agent_disagreements, brief.confidence_ledger = result

    trace("Critic & Verifier Node", "OK",
          f"outputs challenged and verified | confidence adjusted to: {brief.critic_verdict.confidence}")
    trace("Decision Router", "OK",
          f"recommendation: {brief.final_recommendation.value}")
    trace("Output Formatter", "OK", "trade decision brief generated")
    print("-"*60)

    print_disagreement_report(disagreement_analysis)

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
        print("  No active disruption signals detected")
    print(f"\nLive Nigerian Trade Headlines:")
    for a in news.get("articles", [])[:5]:
        print(f"  → {a['title'][:100]}")
    print("="*60)

def print_traceability_report(initial_brief: TradeBrief, revised_brief=None):
    print("\n" + "="*60)
    print("DECISION TRACEABILITY REPORT")
    print("="*60)
    print(f"USD/NGN: {initial_brief.live_data.usd_ngn_rate} ({'LIVE' if initial_brief.live_data.usd_ngn_rate else 'UNAVAILABLE'})")
    print(f"USD/CNY: {initial_brief.live_data.usd_cny_rate} ({'LIVE' if initial_brief.live_data.usd_cny_rate else 'UNAVAILABLE'})")
    print(f"Shipping: USD {initial_brief.live_data.shipping_min}-{initial_brief.live_data.shipping_max} (ESTIMATED)")
    print(f"Data Quality: {initial_brief.live_data.data_quality}")
    print(f"Timestamp: {initial_brief.live_data.data_timestamp}")
    print(f"\nWORKFLOW NODE EXECUTION LOG:")
    for entry in WORKFLOW_TRACE:
        print(entry)
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

def run_tradeflow(raw_query: str, product: str = "goods", quantity: int = 0,
                  origin: str = "China", destination_port: str = "apapa",
                  disruption_type: str = None):

    print("\n" + "="*60)
    print("TRADEFLOW COMMAND SYSTEM")
    print("African Trade Intelligence Platform")
    print("Powered by Microsoft Azure AI Foundry + Foundry IQ")
    print("="*60)
    print(f"Query: {raw_query}")
    print("="*60)

    print("\nPhase 0: Fetching live market intelligence...")
    live_data, news, disruptions = fetch_live_data(product, origin, destination_port)
    print(f"  USD/NGN: {live_data.usd_ngn_rate} ({'LIVE' if live_data.usd_ngn_rate else 'UNAVAILABLE'})")
    print(f"  USD/CNY: {live_data.usd_cny_rate} ({'LIVE' if live_data.usd_cny_rate else 'UNAVAILABLE'})")
    print(f"  Shipping: USD {live_data.shipping_min}-{live_data.shipping_max} (ESTIMATED)")
    print(f"  Disruption Risk: {disruptions.get('risk_level')}")
    print(f"  News Articles: {news.get('count', 0)} live headlines")

    print_news_intelligence(news, disruptions)

    query = TradeQuery(
        raw=raw_query, product=product, quantity=quantity,
        origin=origin, destination="Nigeria"
    )

    print("\nPhase 1: Initial Trade Intelligence Analysis")
    initial_brief = run_agent_chain(query, live_data)
    print_brief(initial_brief, "INITIAL ASSESSMENT")

    revised_brief = None

    if disruption_type and disruption_type in DISRUPTIONS:
        disruption_message = DISRUPTIONS[disruption_type]
        print("\n" + "!"*60)
        print("DISRUPTION SIGNAL RECEIVED — TRIGGERING RE-ANALYSIS")
        print("!"*60)
        print(disruption_message)
        print("!"*60)
        print("\nPhase 2: Re-analyzing with disruption context...")

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
        disruption_type="port_closure"
    )
