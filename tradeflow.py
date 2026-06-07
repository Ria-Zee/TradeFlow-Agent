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

def print_trace(agent_output, step_number: int, total_steps: int):
    print(f"\n--- REASONING TRACE: {agent_output.agent_name} [{step_number}/{total_steps}] ---")
    print(f"Confidence: {agent_output.confidence}")
    if agent_output.assumptions:
        print("Assumptions made:")
        for a in agent_output.assumptions:
            print(f"  * {a}")
    if agent_output.flags:
        print("Data flags:")
        for f in agent_output.flags:
            print(f"  ! {f}")
    print(f"Analysis preview: {agent_output.analysis[:200]}...")
    print("-"*60)

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
    print_trace(brief.market_intel, 1, 4)

    print("  [2/4] Route and Logistics Agent...")
    brief.route_logistics = route_logistics.run(effective_query, brief.market_intel.analysis)
    print_trace(brief.route_logistics, 2, 4)

    print("  [3/4] Risk and Compliance Agent...")
    brief.risk_compliance = risk_compliance.run(effective_query, brief.market_intel.analysis, brief.route_logistics.analysis)
    print_trace(brief.risk_compliance, 3, 4)

    print("  [4/4] Critic and Verifier Agent...")
    brief.critic_verdict = critic.run(effective_query, brief.market_intel, brief.route_logistics, brief.risk_compliance)
    print_trace(brief.critic_verdict, 4, 4)

    return brief

def print_brief(brief: TradeBrief, label: str):
    print("\n" + "="*60)
    print(f"TRADE DECISION BRIEF: {label}")
    print("="*60)
    print(brief.critic_verdict.analysis)
    print("="*60)

def print_traceability_report(initial_brief: TradeBrief, revised_brief: TradeBrief = None):
    print("\n" + "="*60)
    print("DECISION TRACEABILITY REPORT")
    print("="*60)
    print("Agent Chain: Market Intel -> Route Logistics -> Risk Compliance -> Critic")
    print(f"\nINITIAL ANALYSIS:")
    print(f"  Market Intel Confidence:    {initial_brief.market_intel.confidence}")
    print(f"  Route Logistics Confidence: {initial_brief.route_logistics.confidence}")
    print(f"  Risk Compliance Confidence: {initial_brief.risk_compliance.confidence}")
    print(f"  Final Verdict Confidence:   {initial_brief.critic_verdict.confidence}")
    print(f"\nDATA FLAGS RAISED:")
    all_flags = (
        initial_brief.market_intel.flags +
        initial_brief.route_logistics.flags +
        initial_brief.risk_compliance.flags
    )
    for flag in all_flags:
        print(f"  ! {flag}")
    print(f"\nASSUMPTIONS REQUIRING VERIFICATION:")
    all_assumptions = (
        initial_brief.market_intel.assumptions +
        initial_brief.route_logistics.assumptions +
        initial_brief.risk_compliance.assumptions
    )
    for assumption in all_assumptions:
        print(f"  * {assumption}")
    if revised_brief:
        print(f"\nDISRUPTION IMPACT:")
        print(f"  Confidence before disruption: {initial_brief.critic_verdict.confidence}")
        print(f"  Confidence after disruption:  {revised_brief.critic_verdict.confidence}")
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

        revised_brief = run_agent_chain(query, disruption_message)
        print_brief(revised_brief, "REVISED ASSESSMENT POST-DISRUPTION")

    print_traceability_report(initial_brief, revised_brief)

    return revised_brief if revised_brief else initial_brief

if __name__ == "__main__":
    query = "I want to import 500 units of Samsung smartphones from China to Lagos via Apapa port."
    run_tradeflow(query, disruption_type="port_closure")
