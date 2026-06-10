from core.client import MessageRole, get_agents_client, is_agent_service_available, MODEL
from core.models import TradeQuery, AgentOutput, ConfidenceLevel, LiveDataContext
from core.search import search_knowledge
import json

INSTRUCTIONS = (
    "You are an International Trade Risk and Regulatory Intelligence Specialist. "
    "Your responsibility is to identify anything that could block, delay, or materially impact the trade. "
    "Primary Objective: Assess operational, regulatory, legal, supplier, and financial risks. "
    "Analyze: certifications, licensing requirements, compliance obligations, supplier risk, geopolitical risk, FX volatility, fraud indicators, customs requirements. "
    "Questions To Answer: What could go wrong? What regulations apply? Which risks require mitigation? What verification steps are necessary? "
    "Required Output: Compliance Requirements, Risk Register, Critical Risks, Mitigation Actions, Confidence Level. "
    "Guardrails: Never claim regulatory certainty without evidence. Clearly identify areas requiring professional verification with SON, NAFDAC, NCC, Nigeria Customs. "
    "You will receive FOUNDRY IQ regulatory knowledge - use it as your primary reference. "
    "Return your analysis as valid JSON: "
    '{"compliance_requirements": ["string"], '
    '"risk_register": [{"risk": "string", "severity": "HIGH|MEDIUM|LOW", "mitigation": "string"}], '
    '"critical_risks": ["string"], "mitigation_actions": ["string"], '
    '"key_findings": ["string"], "assumptions": ["string"], "confidence": "HIGH|MEDIUM|LOW", "confidence_rationale": "string"}'
)

def run(query: TradeQuery, live_data: LiveDataContext, market_intel_analysis: str, route_analysis: str) -> AgentOutput:
    if not is_agent_service_available():
        from core.local_analysis import risk_compliance as local_risk_compliance
        return local_risk_compliance(query, live_data, market_intel_analysis, route_analysis)

    client = get_agents_client()
    agent = client.create_agent(
        model=MODEL,
        name="tradeflow-risk-compliance",
        instructions=INSTRUCTIONS,
    )
    thread = client.threads.create()

    kb_results = search_knowledge(f"SONCAP NCC NAFDAC certification {query.product} Nigeria import compliance")

    prompt = (
        f"Trade Query: {query.raw}\n"
        f"Product: {query.product} | Quantity: {query.quantity} | "
        f"Origin: {query.origin} | Destination: {query.destination}\n\n"
        f"LIVE DATA:\n"
        f"- USD/NGN: {live_data.usd_ngn_rate} (for FX risk assessment)\n\n"
        f"FOUNDRY IQ REGULATORY KNOWLEDGE:\n{kb_results}\n\n"
        f"Market Intelligence Context:\n{market_intel_analysis}\n\n"
        f"Logistics Context:\n{route_analysis}\n\n"
        + (f"DISRUPTION CONTEXT: {query.disruption_context}\n\n" if query.disruption_context else "")
        + "Using the regulatory knowledge above, provide Compliance Requirements, Risk Register, "
        "Critical Risks, Mitigation Actions, and Confidence Level. Return as valid JSON."
    )

    client.messages.create(thread_id=thread.id, role=MessageRole.USER, content=prompt)
    client.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)

    messages = client.messages.list(thread_id=thread.id)
    raw_analysis = ""
    for msg in messages:
        if msg.text_messages:
            raw_analysis = msg.text_messages[-1].text.value
            break

    client.delete_agent(agent.id)

    try:
        clean = raw_analysis.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        parsed = json.loads(clean.strip())
        confidence = ConfidenceLevel(parsed.get("confidence", "MEDIUM"))
        analysis = (
            f"COMPLIANCE REQUIREMENTS:\n" + "\n".join(f"- {r}" for r in parsed.get("compliance_requirements", [])) +
            f"\n\nCRITICAL RISKS:\n" + "\n".join(f"- {r}" for r in parsed.get("critical_risks", [])) +
            f"\n\nMITIGATION ACTIONS:\n" + "\n".join(f"- {m}" for m in parsed.get("mitigation_actions", []))
        )
        key_findings = parsed.get("key_findings", [])
        assumptions = parsed.get("assumptions", [])
        risk_items = parsed.get("critical_risks", [])
    except Exception:
        confidence = ConfidenceLevel.MEDIUM
        analysis = raw_analysis
        key_findings = []
        assumptions = ["Parse error - see raw analysis"]
        risk_items = []

    return AgentOutput(
        agent_name="Risk and Compliance Agent (Foundry IQ)",
        analysis=analysis,
        confidence=confidence,
        assumptions=assumptions,
        flags=["FOUNDRY_IQ_GROUNDED", "REGULATORY_VERIFICATION_REQUIRED", "FOUNDRY_AGENT_SERVICE"],
        risk_items=risk_items,
        key_findings=key_findings,
    )
