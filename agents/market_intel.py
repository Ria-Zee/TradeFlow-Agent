from azure.ai.agents.models import MessageRole
from core.client import get_agents_client, MODEL
from core.models import TradeQuery, AgentOutput

INSTRUCTIONS = (
    "You are TradeFlow Market Intelligence Agent, running on Microsoft Azure AI Foundry. "
    "Your role is to analyze market conditions for African import/export trade decisions. "
    "You are NOT a calculator. You are an intelligence analyst. "
    "Always flag estimates as ESTIMATED. Never fabricate specific tariff rates or exchange rates as exact facts. "
    "Always distinguish between what you know and what you are estimating. "
    "Be specific to Nigerian/African trade context. "
    "End every analysis with a CONFIDENCE LEVEL: HIGH, MEDIUM, or LOW with justification."
)

def run(query: TradeQuery) -> AgentOutput:
    client = get_agents_client()

    agent = client.create_agent(
        model=MODEL,
        name="tradeflow-market-intel",
        instructions=INSTRUCTIONS,
    )

    thread = client.threads.create()

    prompt = (
        f"Analyze market conditions for this trade query: {query.raw}\n\n"
        f"Product: {query.product} | Quantity: {query.quantity} | "
        f"Origin: {query.origin} | Destination: {query.destination}\n\n"
        "Provide:\n"
        "1. EXCHANGE RATE CONTEXT: USD/NGN environment and volatility risk. Flag as ESTIMATED.\n"
        "2. IMPORT DUTY ESTIMATE: HS code category and estimated duty rate. Flag as ESTIMATED.\n"
        "3. MARKET DEMAND SIGNAL: Is there strong demand for this product?\n"
        "4. PRICING INTELLIGENCE: Estimated landed cost range per unit. Flag as ESTIMATED.\n"
        "5. ASSUMPTIONS: List every assumption explicitly.\n"
        "6. CONFIDENCE LEVEL: HIGH, MEDIUM, or LOW with justification."
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
        agent_name="Market Intelligence Agent (Foundry)",
        analysis=analysis,
        confidence=confidence,
        assumptions=["Exchange rates estimated", "Duty rates require Nigeria Customs verification"],
        flags=["EXCHANGE_RATE_ESTIMATED", "DUTY_RATE_ESTIMATED", "FOUNDRY_AGENT_SERVICE"]
    )
