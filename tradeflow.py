import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import TradeQuery, TradeBrief
from agents import market_intel, route_logistics, risk_compliance, critic

DISRUPTIONS = {
    "port_closure": "DISRUPTION ALERT: Apapa port has been closed due to a labor strike. All cargo operations suspended indefinitely.",
    "fx_spike": "DISRUPTION ALERT: The Naira has devalued sharply. USD/NGN has spiked 15% in the last 24 hours due to CBN policy change.",
    "policy_change": "DISRUPTION ALERT: Nigerian Customs has issued an emergency directive imposing a new 30-day pre-shipment inspection requirement on all electronics imports.",
    "supplier_risk": "DISRUPTION ALERT: A major fraud alert has been issued for electronics suppliers in Shenzhen. Several Nigerian importers have reported receiving counterfeit goods.",
}

def run_agent_chain(query: TradeQuery, disruption_context: str = "") -> TradeBrief:
    brief = TradeBrief(query=query)
    effective_query = TradeQuery(
        raw=query.raw + (f"\n\nCRITICAL CONTEXT: {disruption_context}" if disruption_context else ""),
        product=query.product,
        quantity=query.quantity,
        origin=query.origin,
        destination=query.destination
    )

    print("  [1/4] Market Intelligence Agent...")
    brief.market_intel = market_intel.run(effective_query)
    print(f"        Confidence: {brief.market_intel.confidence}")

    print("  [2/4] Route and Logistics Agent...")
    brief.route_logistics = route_logistics.run(effective_query, brief.market_intel.analysis)
    print(f"        Confidence: {brief.route_logistics.confidence}")

    print("  [3/4] Risk and Compliance Agent...")
    brief.risk_compliance = risk_compliance.run(effective_query, brief.market_intel.analysis, brief.route_logistics.analysis)
    print(f"        Confidence: {brief.risk_compliance.confidence}")

    print("  [4/4] Critic and Verifier Agent...")
    brief.critic_verdict = critic.run(effective_query, brief.market_intel, brief.route_logistics, brief.risk_compliance)
    print(f"        Confidence: {brief.critic_verdict.confidence}")

    return brief

def print_brief(brief: TradeBrief, label: str):
    print("\n" + "="*60)
    print(f"TRADE DECISION BRIEF: {label}")
    print("="*60)
    print(brief.critic_verdict.analysis)
    print("="*60)

def run_tradeflow(raw_query: str, disruption_type: str = None):
    print("\n" + "="*60)
    print("TRADEFLOW COMMAND SYSTEM")
    print("African Trade Intelligence Platform")
    print("="*60)
    print(f"Query: {raw_query}")
    print("="*60)

    query = TradeQuery(
        raw=raw_query,
        product="goods",
        quantity=0,
        origin="China",
        destination="Nigeria"
    )

    print("\nPHASE 1: Initial Trade Intelligence Analysis")
    print("-"*60)
    initial_brief = run_agent_chain(query)
    print_brief(initial_brief, "INITIAL ASSESSMENT")

    if disruption_type and disruption_type in DISRUPTIONS:
        disruption_message = DISRUPTIONS[disruption_type]

        print("\n" + "!"*60)
        print("DISRUPTION SIGNAL RECEIVED")
        print("!"*60)
        print(disruption_message)
        print("!"*60)
        print("\nPHASE 2: Re-analyzing with disruption context...")
        print("-"*60)

        revised_brief = run_agent_chain(query, disruption_message)
        print_brief(revised_brief, "REVISED ASSESSMENT POST-DISRUPTION")

        print("\n" + "="*60)
        print("DISRUPTION IMPACT SUMMARY")
        print("="*60)
        print(f"Initial Confidence:  {initial_brief.critic_verdict.confidence}")
        print(f"Revised Confidence:  {revised_brief.critic_verdict.confidence}")
        print("\nSystem has re-analyzed your trade decision in light")
        print("of the disruption. Review revised brief before proceeding.")
        print("="*60)
        return revised_brief

    return initial_brief

if __name__ == "__main__":
    query = "I want to import 500 units of Samsung smartphones from China to Lagos via Apapa port."
    run_tradeflow(query, disruption_type="port_closure")
