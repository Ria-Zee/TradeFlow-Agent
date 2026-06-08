from azure.ai.agents.models import MessageRole
from core.client import get_agents_client, MODEL
from core.models import TradeQuery, AgentOutput

INSTRUCTIONS = (
    "You are TradeFlow Route and Logistics Agent, running on Microsoft Azure AI Foundry. "
    "Your role is to analyze shipping routes, port conditions, and logistics options for African trade decisions. "
    "You are NOT a shipping calculator. You are a logistics intelligence analyst. "
    "Always flag estimates as ESTIMATED. Never fabricate specific freight rates as exact facts. "
    "Be specific to Nigerian/African port conditions and trade lanes. "
    "Consider Apapa, Tincan, Cotonou, and other West African port alternatives where relevant. "
    "End every analysis with a CONFIDENCE LEVEL: HIGH, MEDIUM, or LOW with justification."
)

def run(query: TradeQuery, market_intel_analysis: str) -> AgentOutput:
    client = get_agents_client()

    agent = client.create_agent(
        model=MODEL,
        name="tradeflow-route-logistics",
        instructions=INSTRUCTIONS,
    )

    thread = client.threads.create()

    prompt = (
        f"Analyze logistics and routing for: {query.raw}\n\n"
        f"Product: {query.product} | Quantity: {query.quantity} | "
        f"Origin: {query.origin} | Destination: {query.destination}\n\n"
        f"Market Intelligence Context:\n{market_intel_analysis}\n\n"
        "Provide:\n"
        "1. PRIMARY ROUTE: Best shipping route with reasoning.\n"
        "2. ALTERNATIVE ROUTES: At least one alternative with tradeoffs.\n"
        "3. PORT CONDITIONS: Congestion risks and clearance times. Flag as ESTIMATED.\n"
        "4. TRANSIT TIME: Estimated shipping duration. Flag as ESTIMATED.\n"
        "5. FREIGHT COST RANGE: Estimated freight cost. Flag as ESTIMATED.\n"
        "6. INCOTERMS RECOMMENDATION: Recommended trade terms and why.\n"
        "7. DOCUMENTATION REQUIRED: Key shipping documents needed.\n"
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
        agent_name="Route and Logistics Agent (Foundry)",
        analysis=analysis,
        confidence=confidence,
        assumptions=["Port conditions based on general knowledge", "Freight rates require live quote"],
        flags=["FREIGHT_COST_ESTIMATED", "TRANSIT_TIME_ESTIMATED", "FOUNDRY_AGENT_SERVICE"]
    )
