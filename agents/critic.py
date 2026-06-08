from azure.ai.agents.models import MessageRole
from core.client import get_agents_client, MODEL
from core.models import TradeQuery, AgentOutput

INSTRUCTIONS = (
    "You are TradeFlow Critic and Verifier Agent, running on Microsoft Azure AI Foundry. "
    "Your role is to review outputs from three specialist agents and produce a final verified trade intelligence verdict. "
    "You are the last line of defence before a recommendation reaches the trader. "
    "Be direct and decisive. The trader needs a clear recommendation. "
    "Do not repeat analysis already provided. Synthesize and add value. "
    "End with a clear verdict: PROCEED, PROCEED WITH CAUTION, or PAUSE AND INVESTIGATE."
)

def run(query: TradeQuery, market_intel, route_logistics, risk_compliance) -> AgentOutput:
    client = get_agents_client()

    agent = client.create_agent(
        model=MODEL,
        name="tradeflow-critic-verifier",
        instructions=INSTRUCTIONS,
    )

    thread = client.threads.create()

    prompt = (
        f"Original Trade Query: {query.raw}\n\n"
        f"MARKET INTELLIGENCE:\n{market_intel.analysis}\n\n"
        f"ROUTE AND LOGISTICS:\n{route_logistics.analysis}\n\n"
        f"RISK AND COMPLIANCE:\n{risk_compliance.analysis}\n\n"
        "Your tasks:\n"
        "1. CONSISTENCY CHECK: Do the three outputs contradict each other?\n"
        "2. COMPLETENESS CHECK: Are there critical gaps?\n"
        "3. ASSUMPTION AUDIT: Most critical assumptions the trader must verify.\n"
        "4. CONFIDENCE SYNTHESIS: Overall confidence — HIGH, MEDIUM, or LOW.\n"
        "5. CRITICAL RISKS: Top 3 risks before proceeding.\n"
        "6. FINAL TRADE RECOMMENDATION: PROCEED, PROCEED WITH CAUTION, or PAUSE AND INVESTIGATE.\n"
        "7. NEXT STEPS: Exactly 3 concrete next steps.\n"
        "8. FINAL VERDICT: One sentence the trader can act on immediately."
    )

    client.messages.create(
        thread_id=thread.id,
        role=MessageRole.USER,
        content=prompt,
    )

    run = client.runs.create_and_process(
        thread_id=thread.id,
        agent_id=agent.id,
    )

    messages = client.messages.list(thread_id=thread.id)
    analysis = ""
    for msg in messages:
        if msg.text_messages:
            analysis = msg.text_messages[-1].text.value
            break

    client.delete_agent(agent.id)

    confidence = "MEDIUM"
    if "PROCEED WITH CAUTION" in analysis.upper():
        confidence = "MEDIUM"
    elif "PAUSE AND INVESTIGATE" in analysis.upper():
        confidence = "LOW"
    elif "CONFIDENCE LEVEL: HIGH" in analysis.upper():
        confidence = "HIGH"

    return AgentOutput(
        agent_name="Critic and Verifier Agent (Foundry)",
        analysis=analysis,
        confidence=confidence,
        assumptions=[],
        flags=["FINAL_VERDICT", "FOUNDRY_AGENT_SERVICE"]
    )
