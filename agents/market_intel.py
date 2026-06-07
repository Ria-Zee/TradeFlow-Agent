from core.client import get_client, MODEL
from core.models import TradeQuery, AgentOutput

def run(query: TradeQuery) -> AgentOutput:
    client = get_client()

    prompt = f"""You are TradeFlow Market Intelligence Agent.

Your role is to analyze market conditions for an African import/export trade decision.
You are NOT a calculator. You are an intelligence analyst.

Trade Query: {query.raw}
Product: {query.product}
Quantity: {query.quantity}
Origin: {query.origin}
Destination: {query.destination}

Analyze and provide:
1. EXCHANGE RATE CONTEXT: Current USD/NGN environment and volatility risk. Flag as ESTIMATED.
2. IMPORT DUTY ESTIMATE: Applicable HS code category and estimated duty rate for this product into Nigeria. Flag as ESTIMATED.
3. MARKET DEMAND SIGNAL: Is there strong market demand for this product in the destination market?
4. PRICING INTELLIGENCE: Estimated landed cost range per unit. Flag as ESTIMATED.
5. ASSUMPTIONS: List every assumption you are making explicitly.
6. CONFIDENCE LEVEL: Rate your overall confidence as HIGH, MEDIUM, or LOW with justification.

Rules:
- Never fabricate specific tariff rates as exact facts. Always flag estimates as ESTIMATED.
- Always distinguish between what you know and what you are estimating.
- Be specific to Nigerian/African trade context.
- End with a one-sentence market intelligence verdict."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a senior trade intelligence analyst specializing in African import/export markets. You reason carefully, flag uncertainty, and never fabricate data."},
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
        agent_name="Market Intelligence Agent",
        analysis=analysis,
        confidence=confidence,
        assumptions=["Exchange rates are estimates based on general knowledge", "Duty rates require verification with Nigeria Customs"],
        flags=["EXCHANGE_RATE_ESTIMATED", "DUTY_RATE_ESTIMATED"]
    )
