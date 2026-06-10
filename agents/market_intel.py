from azure.ai.agents.models import MessageRole
from core.client import get_agents_client, MODEL
from core.models import TradeQuery, AgentOutput, ConfidenceLevel, LiveDataContext
from core.search import search_knowledge
import json

INSTRUCTIONS = (
    "You are a Trade Economist and Market Intelligence Specialist. "
    "You evaluate the commercial viability of proposed trade activities. "
    "Primary Objective: Determine whether the proposed trade activity is financially attractive. "
    "Analyze: exchange rates, landed cost estimates, duties and tariffs, demand signals, profitability indicators, pricing assumptions, market conditions. "
    "Questions To Answer: Is the trade economically viable? What are the primary cost drivers? What assumptions have the greatest impact? What information is missing? "
    "Required Output: Economic Assessment, Cost Drivers, Financial Risks, Assumptions, Confidence Level. "
    "Guardrails: Never fabricate market data. Clearly identify estimated calculations. Differentiate facts from projections. "
    "You will receive LIVE exchange rate data and FOUNDRY IQ knowledge base excerpts - use these as your primary sources. "
    "Return your analysis as valid JSON: "
    '{"economic_assessment": "string", "cost_drivers": ["string"], "financial_risks": ["string"], '
    '"key_findings": ["string"], "assumptions": ["string"], "confidence": "HIGH|MEDIUM|LOW", '
    '"confidence_rationale": "string", "data_sources": ["string"]}'
)

def run(query: TradeQuery, live_data: LiveDataContext) -> AgentOutput:
    client = get_agents_client()
    agent = client.create_agent(
        model=MODEL,
        name="tradeflow-market-intel",
        instructions=INSTRUCTIONS,
    )
    thread = client.threads.create()

    kb_results = search_knowledge(f"{query.product} import duty Nigeria tariff {query.origin}")
    
    from core.tools import get_trade_news
    news_data = get_trade_news(query.product, query.origin, query.destination)
    news_headlines = "\n".join([f"- {a['title']}" for a in news_data.get("articles", [])[:4]])

    fx_context = (
        f"LIVE EXCHANGE RATE DATA (verified, use exact figures):\n"
        f"- USD/NGN: {live_data.usd_ngn_rate} (LIVE as of {live_data.data_timestamp})\n"
        f"- USD/CNY: {live_data.usd_cny_rate} (LIVE)\n"
        f"- CNY/NGN: {live_data.cny_ngn_rate} (LIVE)\n"
        f"- Shipping estimate: USD {live_data.shipping_min}-{live_data.shipping_max} per container (ESTIMATED)\n"
    )

    prompt = (
        f"Trade Query: {query.raw}\n"
        f"Product: {query.product} | Quantity: {query.quantity} | "
        f"Origin: {query.origin} | Destination: {query.destination}\n\n"
        f"{fx_context}\n"
        f"LIVE TRADE NEWS (Nigerian market context):\n{news_headlines}\n\n" 
        f"FOUNDRY IQ KNOWLEDGE BASE (African trade reference data):\n{kb_results}\n\n"
        + (f"DISRUPTION CONTEXT: {query.disruption_context}\n\n" if query.disruption_context else "")
        + "Using the live data and knowledge base above as primary sources, provide your "
        "Economic Assessment, Cost Drivers, Financial Risks, Assumptions, and Confidence Level. "
        "Cite the knowledge base where relevant. Return as valid JSON."
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
            f"ECONOMIC ASSESSMENT:\n{parsed.get('economic_assessment', '')}\n\n"
            f"COST DRIVERS:\n" + "\n".join(f"- {d}" for d in parsed.get("cost_drivers", [])) +
            f"\n\nFINANCIAL RISKS:\n" + "\n".join(f"- {r}" for r in parsed.get("financial_risks", []))
        )
        key_findings = parsed.get("key_findings", [])
        assumptions = parsed.get("assumptions", [])
        risk_items = parsed.get("financial_risks", [])
        data_sources = parsed.get("data_sources", [])
    except Exception:
        confidence = ConfidenceLevel.MEDIUM
        analysis = raw_analysis
        key_findings = []
        assumptions = ["Parse error - see raw analysis"]
        risk_items = []
        data_sources = []

    return AgentOutput(
        agent_name="Market Intelligence Agent (Foundry IQ + Live FX)",
        analysis=analysis,
        confidence=confidence,
        assumptions=assumptions + [f"Live USD/NGN: {live_data.usd_ngn_rate}"],
        flags=["LIVE_FX_DATA", "FOUNDRY_IQ_GROUNDED", "FOUNDRY_AGENT_SERVICE"],
        risk_items=risk_items,
        key_findings=key_findings,
    )
