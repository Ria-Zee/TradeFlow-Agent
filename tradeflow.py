import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import TradeQuery, TradeBrief
from agents import market_intel, route_logistics, risk_compliance, critic

def run_tradeflow(raw_query: str) -> TradeBrief:
    print("\n" + "="*60)
    print("TRADEFLOW AGENT - AFRICAN TRADE INTELLIGENCE SYSTEM")
    print("="*60)
    print(f"Query: {raw_query}")
    print("="*60 + "\n")

    query = TradeQuery(
        raw=raw_query,
        product="goods",
        quantity=0,
        origin="unknown",
        destination="Nigeria"
    )

    brief = TradeBrief(query=query)

    print("[1/4] Market Intelligence Agent running...")
    brief.market_intel = market_intel.run(query)
    print(f"      Confidence: {brief.market_intel.confidence}")
    print(f"      Flags: {', '.join(brief.market_intel.flags)}\n")

    print("[2/4] Route and Logistics Agent running...")
    brief.route_logistics = route_logistics.run(query, brief.market_intel.analysis)
    print(f"      Confidence: {brief.route_logistics.confidence}")
    print(f"      Flags: {', '.join(brief.route_logistics.flags)}\n")

    print("[3/4] Risk and Compliance Agent running...")
    brief.risk_compliance = risk_compliance.run(query, brief.market_intel.analysis, brief.route_logistics.analysis)
    print(f"      Confidence: {brief.risk_compliance.confidence}")
    print(f"      Flags: {', '.join(brief.risk_compliance.flags)}\n")

    print("[4/4] Critic and Verifier Agent running...")
    brief.critic_verdict = critic.run(query, brief.market_intel, brief.route_logistics, brief.risk_compliance)
    print(f"      Confidence: {brief.critic_verdict.confidence}\n")

    print("="*60)
    print("FINAL TRADE DECISION BRIEF")
    print("="*60)
    print(brief.critic_verdict.analysis)
    print("="*60 + "\n")

    return brief

if __name__ == "__main__":
    query = "I want to import 500 units of Samsung smartphones from China to Lagos via Apapa port."
    run_tradeflow(query)
