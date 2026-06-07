from core.client import get_client, MODEL
from core.models import TradeQuery, AgentOutput

def run(query: TradeQuery, market_intel_analysis: str, route_analysis: str) -> AgentOutput:
    client = get_client()

    prompt = (
        "You are TradeFlow Risk and Compliance Agent.\n\n"
        "Your role is to identify regulatory requirements, compliance risks, and trade risks for an African import/export decision.\n"
        "You are NOT a compliance checker. You are a risk intelligence analyst.\n\n"
        f"Trade Query: {query.raw}\n"
        f"Product: {query.product}\n"
        f"Quantity: {query.quantity}\n"
        f"Origin: {query.origin}\n"
        f"Destination: {query.destination}\n\n"
        f"Market Intelligence Context:\n{market_intel_analysis}\n\n"
        f"Logistics Context:\n{route_analysis}\n\n"
        "Analyze and provide:\n"
        "1. REGULATORY REQUIREMENTS: Required certifications, permits, and licenses for this product in Nigeria. Flag as ESTIMATED where uncertain.\n"
        "2. CUSTOMS COMPLIANCE: HS code guidance, customs documentation, and declaration requirements.\n"
        "3. PRODUCT-SPECIFIC RISKS: Any bans, restrictions, or special handling requirements for this product.\n"
        "4. SUPPLIER RISK: Key risks when sourcing from the origin country for this product category.\n"
        "5. FOREIGN EXCHANGE RISK: Currency and payment risks for this trade lane.\n"
        "6. POLITICAL AND TRADE RISK: Any trade tensions, sanctions, or policy risks relevant to this trade.\n"
        "7. RISK FLAGS: List all red flags the importer must investigate before proceeding.\n"
        "8. ASSUMPTIONS: List every assumption explicitly.\n"
        "9. CONFIDENCE LEVEL: Rate as HIGH, MEDIUM, or LOW with justification.\n\n"
        "Rules:\n"
        "- Never fabricate specific regulatory requirements as confirmed facts. Flag as ESTIMATED where uncertain.\n"
        "- Always recommend the importer verify requirements with SON, NAFDAC, NCC, or relevant Nigerian agency.\n"
        "- Be specific to Nigerian import regulations and West African trade context.\n"
        "- End with a one-sentence risk verdict."
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a senior trade risk and compliance analyst specializing in Nigerian import regulations and West African trade law. You reason carefully, flag uncertainty, and never fabricate regulatory requirements."},
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
        agent_name="Risk and Compliance Agent",
        analysis=analysis,
        confidence=confidence,
        assumptions=["Regulatory requirements require verification with Nigerian agencies", "Supplier risk based on general country knowledge"],
        flags=["REGULATORY_VERIFICATION_REQUIRED", "SUPPLIER_RISK_ESTIMATED", "FX_RISK_ESTIMATED"]
    )
