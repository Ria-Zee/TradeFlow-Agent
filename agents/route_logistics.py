from core.client import get_client, MODEL
from core.models import TradeQuery, AgentOutput

def run(query: TradeQuery, market_intel_analysis: str) -> AgentOutput:
    client = get_client()

    prompt = (
        "You are TradeFlow Route and Logistics Agent.\n\n"
        "Your role is to analyze shipping routes, port conditions, and logistics options for an African trade decision.\n"
        "You are NOT a shipping calculator. You are a logistics intelligence analyst.\n\n"
        f"Trade Query: {query.raw}\n"
        f"Product: {query.product}\n"
        f"Quantity: {query.quantity}\n"
        f"Origin: {query.origin}\n"
        f"Destination: {query.destination}\n\n"
        f"Market Intelligence Context:\n{market_intel_analysis}\n\n"
        "Analyze and provide:\n"
        "1. PRIMARY ROUTE: Best shipping route from origin to destination with reasoning.\n"
        "2. ALTERNATIVE ROUTES: At least one alternative route with tradeoffs.\n"
        "3. PORT CONDITIONS: Known congestion risks and clearance time estimates. Flag as ESTIMATED.\n"
        "4. TRANSIT TIME: Estimated shipping duration. Flag as ESTIMATED.\n"
        "5. FREIGHT COST RANGE: Estimated freight cost. Flag as ESTIMATED.\n"
        "6. INCOTERMS RECOMMENDATION: Recommended trade terms and why.\n"
        "7. DOCUMENTATION REQUIRED: Key shipping documents needed.\n"
        "8. ASSUMPTIONS: List every assumption explicitly.\n"
        "9. CONFIDENCE LEVEL: Rate as HIGH, MEDIUM, or LOW with justification.\n\n"
        "Rules:\n"
        "- Never fabricate specific freight rates as exact facts. Always flag as ESTIMATED.\n"
        "- Be specific to Nigerian/African port conditions and trade lanes.\n"
        "- Consider Apapa, Tincan, Cotonou alternatives where relevant.\n"
        "- End with a one-sentence logistics verdict."
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a senior logistics intelligence analyst specializing in West African trade lanes and port operations. You reason carefully, flag uncertainty, and never fabricate data."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    analysis = response.choices[0].message.content

    confidence = "MEDIUM"
    if "HIGH confidence" in analysis.upper():
        confidence = "HIGH"
    elif "LOW confidence" in analysis.upper():
        confidence = "LOW"

    return AgentOutput(
        agent_name="Route and Logistics Agent",
        analysis=analysis,
        confidence=confidence,
        assumptions=["Port conditions based on general knowledge", "Freight rates require live quote from freight forwarder"],
        flags=["FREIGHT_COST_ESTIMATED", "TRANSIT_TIME_ESTIMATED", "PORT_CONDITIONS_ESTIMATED"]
    )
