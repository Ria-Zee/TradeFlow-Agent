from core.client import get_client, MODEL
from core.models import TradeQuery, AgentOutput

def run(query: TradeQuery, market_intel: AgentOutput, route_logistics: AgentOutput, risk_compliance: AgentOutput) -> AgentOutput:
    client = get_client()

    prompt = (
        "You are TradeFlow Critic and Verifier Agent.\n\n"
        "Your role is to review the outputs of three specialist agents and produce a final verified trade intelligence verdict.\n"
        "You are the last line of defence before a recommendation reaches the trader.\n\n"
        f"Original Trade Query: {query.raw}\n\n"
        f"MARKET INTELLIGENCE AGENT OUTPUT:\n{market_intel.analysis}\n\n"
        f"ROUTE AND LOGISTICS AGENT OUTPUT:\n{route_logistics.analysis}\n\n"
        f"RISK AND COMPLIANCE AGENT OUTPUT:\n{risk_compliance.analysis}\n\n"
        "Your tasks:\n"
        "1. CONSISTENCY CHECK: Do the three agent outputs contradict each other? Flag any contradictions.\n"
        "2. COMPLETENESS CHECK: Are there critical gaps in the analysis? What important factors were missed?\n"
        "3. ASSUMPTION AUDIT: List the most critical assumptions across all agents that the trader must verify.\n"
        "4. CONFIDENCE SYNTHESIS: Given all three analyses, what is the overall confidence level? Rate as HIGH, MEDIUM, or LOW.\n"
        "5. CRITICAL RISKS: What are the top 3 risks the trader must address before proceeding?\n"
        "6. FINAL TRADE RECOMMENDATION: Based on all evidence, should the trader PROCEED, PROCEED WITH CAUTION, or PAUSE AND INVESTIGATE? Explain why.\n"
        "7. NEXT STEPS: Give the trader exactly 3 concrete next steps to take.\n\n"
        "Rules:\n"
        "- Be direct and decisive. The trader needs a clear recommendation.\n"
        "- Do not repeat analysis already provided. Synthesize and add value.\n"
        "- Flag any agent output that seems unreliable or incomplete.\n"
        "- End with a one-sentence final verdict the trader can act on."
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a senior trade intelligence director who reviews multi-agent analysis and produces final verified trade recommendations. You are decisive, rigorous, and always act in the best interest of the African trader."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )

    analysis = response.choices[0].message.content

    confidence = "MEDIUM"
    if "HIGH confidence" in analysis.upper() or "PROCEED" in analysis.upper():
        confidence = "HIGH"
    elif "LOW confidence" in analysis.upper() or "PAUSE" in analysis.upper():
        confidence = "LOW"

    return AgentOutput(
        agent_name="Critic and Verifier Agent",
        analysis=analysis,
        confidence=confidence,
        assumptions=[],
        flags=["FINAL_VERDICT"]
    )
