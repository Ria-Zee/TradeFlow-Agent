import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import TradeQuery, TradeBrief, LiveDataContext, TradeRecommendation
from core.tools import get_trade_context
from agents import market_intel, route_logistics, risk_compliance, critic

DISRUPTIONS = {
    "port_closure": "DISRUPTION ALERT: Apapa port has been closed due to a labor strike. All cargo operations suspended indefinitely.",
    "fx_spike": "DISRUPTION ALERT: The Naira has devalued sharply. USD/NGN has spiked 15% in the last 24 hours due to CBN policy change.",
    "policy_change": "DISRUPTION ALERT: Nigerian Customs has issued an emergency directive imposing a new 30-day pre-shipment inspection requirement on all electronics imports.",
    "supplier_risk": "DISRUPTION ALERT: A major fraud alert has been issued for electronics suppliers in Shenzhen. Several Nigerian importers have reported receiving counterfeit goods.",
}

def fetch_live_data(product: str, origin: str, destination: str) -> LiveDataContext:
    print("  Fetching live market data...")
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
    )

def print_trace(agent_output, step: int, total: int):
    print(f"\n--- REASONING TRACE: {agent_output.agent_name} [{step}/{total}] ---")
    print(f"Confidence: {agent_output.confidence}")
    if agent_output.assumptions:
        print("Assumptions:")
        for a in agent_output.assumptions[:3]:
            print(f"  * {a}")
    print(f"Flags: {', '.join(agent_output.flags)}")
    print(f"Preview: {agent_output.analysis[:200]}...")
    print("-"*60)

def run_agent_chain(query: TradeQuery, live_data: LiveDataContext) -> TradeBrief:
    brief = TradeBrief(query=query, live_data=live_data)

    print("  [1/4] Market Intelligence Agent (Foundry IQ + Live FX)...")
    brief.market_intel = market_intel.run(query, live_data)
    print_trace(brief.market_intel, 1, 4)

    print("  [2/4] Route and Logistics Agent (Foundry IQ)...")
    brief.route_logistics = route_logistics.run(query, live_data, brief.market_intel.analysis)
    print_trace(brief.route_logistics, 2, 4)

    print("  [3/4] Risk and Compliance Agent (Foundry IQ)...")
    brief.risk_compliance = risk_compliance.run(query, live_data, brief.market_intel.analysis, brief.route_logistics.analysis)
    print_trace(brief.risk_compliance, 3, 4)

    print("  [4/4] Critic and Verifier Agent...")
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

def print_traceability_report(initial_brief: TradeBrief, revised_brief: TradeBrief = None):
    print("\n" + "="*60)
    print("DECISION TRACEABILITY REPORT")
    print("="*60)
    print(f"Live USD/NGN Rate Used: {initial_brief.live_data.usd_ngn_rate} (LIVE)")
    print(f"Live USD/CNY Rate Used: {initial_brief.live_data.usd_cny_rate} (LIVE)")
    print(f"Shipping Estimate: USD {initial_brief.live_data.shipping_min}-{initial_brief.live_data.shipping_max} (ESTIMATED)")
    print(f"Data Timestamp: {initial_brief.live_data.data_timestamp}")
    print(f"\nAgent Chain: Market Intel → Route Logistics → Risk Compliance → Critic")
    print(f"\nINITIAL CONFIDENCE SCORES:")
    print(f"  Market Intel:     {initial_brief.market_intel.confidence}")
    print(f"  Route Logistics:  {initial_brief.route_logistics.confidence}")
    print(f"  Risk Compliance:  {initial_brief.risk_compliance.confidence}")
    print(f"  Final Verdict:    {initial_brief.critic_verdict.confidence}")
    if initial_brief.confidence_ledger:
        print(f"\nCONFIDENCE LEDGER:")
        print(f"  Score: {initial_brief.confidence_ledger.get('score', 'N/A')}/100")
        raises = initial_brief.confidence_ledger.get('raises_confidence', [])
        lowers = initial_brief.confidence_ledger.get('lowers_confidence', [])
        if raises:
            print(f"  What raises confidence:")
            for r in raises:
                print(f"    + {r}")
        if lowers:
            print(f"  What lowers confidence:")
            for l in lowers:
                print(f"    - {l}")
    if initial_brief.agent_disagreements:
        print(f"\nAGENT DISAGREEMENTS DETECTED:")
        for d in initial_brief.agent_disagreements:
            print(f"  ! {d}")
    print(f"\nFOUNDRY IQ GROUNDING: african-trade-knowledge index")
    all_flags = (
        initial_brief.market_intel.flags +
        initial_brief.route_logistics.flags +
        initial_brief.risk_compliance.flags +
        initial_brief.critic_verdict.flags
    )
    unique_flags = list(dict.fromkeys(all_flags))
    print(f"\nSYSTEM FLAGS: {', '.join(unique_flags)}")
    if revised_brief:
        print(f"\nDISRUPTION IMPACT:")
        print(f"  Confidence before: {initial_brief.critic_verdict.confidence}")
        print(f"  Confidence after:  {revised_brief.critic_verdict.confidence}")
        if revised_brief.agent_disagreements:
            print(f"  New disagreements post-disruption:")
            for d in revised_brief.agent_disagreements:
                print(f"    ! {d}")
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

    live_data = fetch_live_data(product, origin, destination_port)
    print(f"  Live USD/NGN: {live_data.usd_ngn_rate}")
    print(f"  Live USD/CNY: {live_data.usd_cny_rate}")
    print(f"  Shipping estimate: USD {live_data.shipping_min}-{live_data.shipping_max}")

    query = TradeQuery(
        raw=raw_query,
        product=product,
        quantity=quantity,
        origin=origin,
        destination="Nigeria"
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
            raw=raw_query,
            product=product,
            quantity=quantity,
            origin=origin,
            destination="Nigeria",
            disruption_context=disruption_message
        )
        revised_live_data = fetch_live_data(product, origin, destination_port)
        revised_brief = run_agent_chain(disrupted_query, revised_live_data)
        print_brief(revised_brief, "REVISED ASSESSMENT POST-DISRUPTION")

    print_traceability_report(initial_brief, revised_brief)
    return revised_brief if revised_brief else initial_brief

if __name__ == "__main__":
    run_tradeflow(
        raw_query="I want to import 500 units of Samsung smartphones from China to Lagos via Apapa port.",
        product="Samsung smartphones",
        quantity=500,
        origin="China",
        destination_port="apapa",
        disruption_type="port_closure"
    )
