from azure.ai.agents.models import MessageRole
from core.client import get_agents_client, MODEL
from core.models import TradeQuery, AgentOutput

INSTRUCTIONS = (
    "You are TradeFlow Risk and Compliance Agent, running on Microsoft Azure AI Foundry. "
    "Your role is to identify regulatory requirements, compliance risks, and trade risks for African import/export decisions. "
    "You are NOT a compliance checker. You are a risk intelligence analyst. "
    "Never fabricate specific regulatory requirements as confirmed facts. Flag as ESTIMATED where uncertain. "
    "Always recommend the importer verify requirements with SON, NAFDAC, NCC, or relevant Nigerian agency. "
    "Be specific to Nigerian import regulations and West African trade context. "
    "End every analysis with a CONFIDENCE LEVEL: HIGH, MEDIUM, or LOW with justification."
)

def run(query: TradeQuery, market_intel_analysis: str, route_analysis: str) -> AgentOutput:
    client = get_agents_client()

    agent = client.create_agent(
        model=MODEL,
        name="tradeflow-risk-compliance",
        instructions=INSTRUCTIONS,
    )

    thread = client.threads.create()

    prompt = (
        f"Analyze compliance and risk for: {query.raw}\n\n"
        f"Product: {query.product} | Quantity: {query.quantity} | "
        f"Origin: {query.origin} | Destination: {query.destination}\n\n"
        f"Market Intelligence Context:\n{market_intel_analysis}\n\n"
        f"Logistics Context:\n{route_analysis}\n\n"
        "Provide:\n"
        "1. REGULATORY REQUIREMENTS: Required certifications and permits. Flag as ESTIMATED.\n"
        "2. CUSTOMS COMPLIANCE: HS code guidance and documentation.\n"
        "3. PRODUCT-SPECIFIC RISKS: Bans, restrictions, special handling.\n"
        "4. SUPPLIER RISK: Key risks sourcing from origin country.\n"
        "5. FOREIGN EXCHANGE RISK: Currency and payment risks.\n"
        "6. POLITICAL AND TRADE RISK: Trade tensions or policy risks.\n"
        "7. RISK FLAGS: All red flags before proceeding.\n"
        "8. ASSUMPTIONS: List every assumption explicitly.\n"
        "9. CONFIDENCE LEVEL: HIGH, MEDIUM, or LOW with justification."
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
    if "CONFIDENCE LEVEL: HIGH" in analysis.upper():
        confidence = "HIGH"
    elif "CONFIDENCE LEVEL: LOW" in analysis.upper():
        confidence = "LOW"

    return AgentOutput(
        agent_name="Risk and Compliance Agent (Foundry)",
        analysis=analysis,
        confidence=confidence,
        assumptions=["Regulatory requirements need verification with Nigerian agencies"],
        flags=["REGULATORY_VERIFICATION_REQUIRED", "SUPPLIER_RISK_ESTIMATED", "FOUNDRY_AGENT_SERVICE"]
    )
