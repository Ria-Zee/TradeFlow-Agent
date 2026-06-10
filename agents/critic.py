from azure.ai.agents.models import MessageRole
from core.client import get_agents_client, MODEL
from core.models import TradeQuery, AgentOutput, ConfidenceLevel, TradeRecommendation, LiveDataContext
import json

INSTRUCTIONS = (
    "You are the independent reviewer of the entire TradeFlow Command System. "
    "You are responsible for challenging assumptions, identifying contradictions, validating conclusions, and producing the final recommendation. "
    "Primary Objective: Ensure that recommendations are evidence-based, internally consistent, and decision-ready. "
    "Responsibilities: Review all agent outputs, identify conflicts, challenge assumptions, evaluate evidence quality, calculate overall confidence, produce final recommendation. "
    "Recommendation Categories: PROCEED | PROCEED WITH CAUTION | PAUSE AND INVESTIGATE. "
    "Required Output: Executive Summary, Contradictions Found, Evidence Quality Assessment, Confidence Assessment, Final Recommendation, Top Three Next Actions. "
    "Guardrails: Do not blindly accept specialist outputs. Act as a skeptical reviewer. Prefer caution over unsupported certainty. "
    "Reduce confidence when assumptions dominate evidence. Flag unresolved risks. "
    "IMPORTANT: Explicitly identify any disagreements between agents and explain why they disagree. "
    "The final recommendation must be traceable to evidence provided by the specialist agents. "
    "Return your analysis as valid JSON: "
    '{"executive_summary": "string", "contradictions_found": ["string"], "agent_disagreements": ["string"], '
    '"evidence_quality": "HIGH|MEDIUM|LOW", "confidence_assessment": "HIGH|MEDIUM|LOW", '
    '"confidence_rationale": "string", "confidence_score": 0, '
    '"what_raises_confidence": ["string"], "what_lowers_confidence": ["string"], '
    '"final_recommendation": "PROCEED|PROCEED WITH CAUTION|PAUSE AND INVESTIGATE", '
    '"recommendation_rationale": "string", "top_three_actions": ["string"], "final_verdict": "string"}'
)

def run(query: TradeQuery, live_data: LiveDataContext, market_intel, route_logistics, risk_compliance) -> tuple:
    client = get_agents_client()
    agent = client.create_agent(
        model=MODEL,
        name="tradeflow-critic-verifier",
        instructions=INSTRUCTIONS,
    )
    thread = client.threads.create()

    prompt = (
        f"Original Trade Query: {query.raw}\n\n"
        f"LIVE DATA USED: USD/NGN={live_data.usd_ngn_rate}, USD/CNY={live_data.usd_cny_rate}\n"
        f"All agents grounded with Foundry IQ African trade knowledge base.\n\n"
        f"MARKET INTELLIGENCE AGENT (Confidence: {market_intel.confidence}):\n{market_intel.analysis}\n"
        f"Financial Risks: {market_intel.risk_items}\n\n"
        f"ROUTE AND LOGISTICS AGENT (Confidence: {route_logistics.confidence}):\n{route_logistics.analysis}\n"
        f"Logistics Risks: {route_logistics.risk_items}\n\n"
        f"RISK AND COMPLIANCE AGENT (Confidence: {risk_compliance.confidence}):\n{risk_compliance.analysis}\n"
        f"Critical Risks: {risk_compliance.risk_items}\n\n"
        + (f"DISRUPTION CONTEXT: {query.disruption_context}\n\n" if query.disruption_context else "")
        + "Challenge all three outputs. Identify contradictions and agent disagreements explicitly. "
        "Produce a Confidence Ledger showing what would raise and lower confidence. "
        "Provide your Executive Summary, Evidence Quality, Confidence Assessment with score 0-100, "
        "Final Recommendation, and Top Three Next Actions. Return as valid JSON."
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

    recommendation = TradeRecommendation.PAUSE_AND_INVESTIGATE
    final_verdict = ""
    agent_disagreements = []
    confidence_ledger = {}

    try:
        clean = raw_analysis.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        parsed = json.loads(clean.strip())
        confidence = ConfidenceLevel(parsed.get("confidence_assessment", "MEDIUM"))
        rec_str = parsed.get("final_recommendation", "PAUSE AND INVESTIGATE")
        recommendation = TradeRecommendation(rec_str)
        final_verdict = parsed.get("final_verdict", "")
        agent_disagreements = parsed.get("agent_disagreements", [])
        confidence_ledger = {
            "score": parsed.get("confidence_score", 0),
            "raises_confidence": parsed.get("what_raises_confidence", []),
            "lowers_confidence": parsed.get("what_lowers_confidence", [])
        }
        analysis = (
            f"EXECUTIVE SUMMARY:\n{parsed.get('executive_summary', '')}\n\n"
            f"AGENT DISAGREEMENTS:\n" + "\n".join(f"- {d}" for d in agent_disagreements) +
            f"\n\nCONTRADICTIONS:\n" + "\n".join(f"- {c}" for c in parsed.get("contradictions_found", [])) +
            f"\n\nEVIDENCE QUALITY: {parsed.get('evidence_quality', '')}\n"
            f"CONFIDENCE: {parsed.get('confidence_assessment', '')} ({parsed.get('confidence_score', 0)}/100)\n"
            f"RATIONALE: {parsed.get('confidence_rationale', '')}\n\n"
            f"CONFIDENCE LEDGER:\n"
            f"  Raises confidence: " + ", ".join(parsed.get("what_raises_confidence", [])) +
            f"\n  Lowers confidence: " + ", ".join(parsed.get("what_lowers_confidence", [])) +
            f"\n\nFINAL RECOMMENDATION: {rec_str}\n"
            f"RATIONALE: {parsed.get('recommendation_rationale', '')}\n\n"
            f"TOP THREE ACTIONS:\n" + "\n".join(f"{i+1}. {a}" for i, a in enumerate(parsed.get("top_three_actions", [])))
        )
        risk_items = parsed.get("contradictions_found", [])
        key_findings = parsed.get("top_three_actions", [])
        assumptions = []
    except Exception:
        confidence = ConfidenceLevel.MEDIUM
        analysis = raw_analysis
        risk_items = []
        key_findings = []
        assumptions = ["Parse error - see raw analysis"]

    output = AgentOutput(
        agent_name="Critic and Verifier Agent (Foundry)",
        analysis=analysis,
        confidence=confidence,
        assumptions=assumptions,
        flags=["FINAL_VERDICT", "CONFIDENCE_LEDGER", "AGENT_DISAGREEMENT_DETECTION", "FOUNDRY_AGENT_SERVICE"],
        risk_items=risk_items,
        key_findings=key_findings,
    )
    return output, recommendation, final_verdict, agent_disagreements, confidence_ledger
