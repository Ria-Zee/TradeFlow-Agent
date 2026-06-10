from core.client import MessageRole, get_agents_client, is_agent_service_available, MODEL
from core.models import TradeQuery, AgentOutput, ConfidenceLevel, LiveDataContext
from core.search import search_knowledge
import json

INSTRUCTIONS = (
    "You are a Supply Chain Strategist and Logistics Planning Expert. "
    "You evaluate the movement of goods from origin to destination. "
    "Primary Objective: Determine the most practical and cost-effective logistics strategy. "
    "Analyze: shipping routes, ports, freight estimates, transit times, route alternatives, bottlenecks, customs delays, Incoterms implications. "
    "Questions To Answer: What is the recommended route? What alternatives exist? What logistics risks exist? What delays are likely? "
    "Required Output: Recommended Route, Alternative Routes, Logistics Risks, Estimated Timelines, Assumptions, Confidence Level. "
    "Guardrails: Do not present estimates as guaranteed outcomes. Flag all uncertain logistics assumptions. "
    "You will receive FOUNDRY IQ port intelligence data - use it as your primary reference for West African ports. "
    "Return your analysis as valid JSON: "
    '{"recommended_route": "string", "alternative_routes": ["string"], "logistics_risks": ["string"], '
    '"estimated_timeline": "string", "freight_estimate": "string", "incoterms_recommendation": "string", '
    '"key_findings": ["string"], "assumptions": ["string"], "confidence": "HIGH|MEDIUM|LOW", "confidence_rationale": "string"}'
)

def run(query: TradeQuery, live_data: LiveDataContext, market_intel_analysis: str) -> AgentOutput:
    if not is_agent_service_available():
        from core.local_analysis import route_logistics as local_route_logistics
        return local_route_logistics(query, live_data, market_intel_analysis)

    client = get_agents_client()
    agent = client.create_agent(
        model=MODEL,
        name="tradeflow-route-logistics",
        instructions=INSTRUCTIONS,
    )
    thread = client.threads.create()

    kb_results = search_knowledge(f"port {query.destination} shipping route West Africa logistics")

    prompt = (
        f"Trade Query: {query.raw}\n"
        f"Product: {query.product} | Quantity: {query.quantity} | "
        f"Origin: {query.origin} | Destination: {query.destination}\n\n"
        f"LIVE DATA:\n"
        f"- USD/NGN: {live_data.usd_ngn_rate} (use for Naira cost estimates)\n"
        f"- Shipping estimate: USD {live_data.shipping_min}-{live_data.shipping_max} per container, "
        f"{live_data.shipping_transit_days} days (ESTIMATED)\n\n"
        f"FOUNDRY IQ PORT INTELLIGENCE:\n{kb_results}\n\n"
        f"Market Intelligence Context:\n{market_intel_analysis}\n\n"
        + (f"DISRUPTION CONTEXT: {query.disruption_context}\n\n" if query.disruption_context else "")
        + "Using port intelligence above, provide Recommended Route, Alternative Routes, "
        "Logistics Risks, Timelines, and Confidence Level. Return as valid JSON."
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
            f"RECOMMENDED ROUTE:\n{parsed.get('recommended_route', '')}\n\n"
            f"ALTERNATIVE ROUTES:\n" + "\n".join(f"- {r}" for r in parsed.get("alternative_routes", [])) +
            f"\n\nESTIMATED TIMELINE: {parsed.get('estimated_timeline', '')}\n"
            f"FREIGHT ESTIMATE: {parsed.get('freight_estimate', '')}\n"
            f"INCOTERMS: {parsed.get('incoterms_recommendation', '')}"
        )
        key_findings = parsed.get("key_findings", [])
        assumptions = parsed.get("assumptions", [])
        risk_items = parsed.get("logistics_risks", [])
    except Exception:
        confidence = ConfidenceLevel.MEDIUM
        analysis = raw_analysis
        key_findings = []
        assumptions = ["Parse error - see raw analysis"]
        risk_items = []

    return AgentOutput(
        agent_name="Route and Logistics Agent (Foundry IQ)",
        analysis=analysis,
        confidence=confidence,
        assumptions=assumptions,
        flags=["FOUNDRY_IQ_GROUNDED", "FREIGHT_COST_ESTIMATED", "FOUNDRY_AGENT_SERVICE"],
        risk_items=risk_items,
        key_findings=key_findings,
    )
