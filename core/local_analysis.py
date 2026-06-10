from __future__ import annotations

from core.models import AgentOutput, ConfidenceLevel, LiveDataContext, TradeQuery, TradeRecommendation


def _rate_text(rate: float | None) -> str:
    return f"{rate:,.4f}" if isinstance(rate, (int, float)) else "unavailable"


def _product_flags(product: str) -> dict:
    text = product.lower()
    electronics = any(word in text for word in ["phone", "smartphone", "laptop", "computer", "electronics", "inverter", "solar"])
    regulated_food_drug = any(word in text for word in ["food", "drug", "cosmetic", "medicine", "beverage"])
    return {"electronics": electronics, "regulated_food_drug": regulated_food_drug}


def market_intel(query: TradeQuery, live_data: LiveDataContext) -> AgentOutput:
    rate = live_data.usd_ngn_rate
    high_fx = isinstance(rate, (int, float)) and rate >= 1400
    cost_range = "unavailable"
    if rate and live_data.shipping_min and live_data.shipping_max:
        cost_range = f"NGN {live_data.shipping_min * rate:,.0f} - {live_data.shipping_max * rate:,.0f}"

    risks = [
        "FX volatility can materially change landed cost between quote, payment, and customs clearance.",
        "Import duty, VAT, port charges, and clearing costs must be verified before committing capital.",
    ]
    if high_fx:
        risks.insert(0, f"Naira weakness is elevated with USD/NGN around {_rate_text(rate)}.")

    confidence = ConfidenceLevel.MEDIUM if rate else ConfidenceLevel.LOW
    analysis = (
        "ECONOMIC ASSESSMENT:\n"
        f"Local fallback analysis used because Azure AI Agents is not configured. For {query.quantity or 'the requested quantity'} "
        f"units of {query.product}, commercial viability depends primarily on verified supplier price, live FX, duties, "
        "clearing fees, and achievable resale margin.\n\n"
        "COST DRIVERS:\n"
        f"- USD/NGN: {_rate_text(rate)}\n"
        f"- Estimated container freight: USD {live_data.shipping_min}-{live_data.shipping_max}\n"
        f"- Estimated freight translated to Naira: {cost_range}\n"
        "- Customs duty/VAT/levies and terminal handling charges require broker verification.\n\n"
        "FINANCIAL RISKS:\n" + "\n".join(f"- {risk}" for risk in risks)
    )
    data_flag = "LIVE_FX_DATA" if rate else "FX_DATA_UNAVAILABLE"
    return AgentOutput(
        agent_name="Market Intelligence Agent (Local Fallback + Live FX)",
        analysis=analysis,
        confidence=confidence,
        assumptions=[
            "Azure AI Agents service was unavailable, so deterministic fallback rules were used.",
            f"Live USD/NGN: {rate}",
            "Freight is an estimate and excludes destination charges unless separately verified.",
        ],
        flags=["LOCAL_FALLBACK", data_flag, "FREIGHT_COST_ESTIMATED"],
        risk_items=risks,
        key_findings=[
            "Verify landed cost with a licensed customs broker.",
            "Lock FX/payment timing before placing a supplier order.",
        ],
    )


def route_logistics(query: TradeQuery, live_data: LiveDataContext, market_intel_analysis: str) -> AgentOutput:
    destination = (query.destination or "Nigeria").lower()
    raw = query.raw.lower()
    port = "Apapa" if "apapa" in raw or "nigeria" in destination else query.destination or "destination port"
    if "cotonou" in raw:
        port = "Cotonou"

    risks = [
        "Freight and sailing schedules can shift before booking confirmation.",
        "Port congestion, documentation errors, or customs examinations can extend clearance timelines.",
    ]
    if port.lower() == "apapa":
        risks.append("Apapa may face Lagos port congestion and inland trucking delays.")
    if query.disruption_context:
        risks.insert(0, "Active disruption context may invalidate the preferred routing plan.")

    confidence = ConfidenceLevel.MEDIUM if live_data.shipping_min and live_data.shipping_max else ConfidenceLevel.LOW
    analysis = (
        f"RECOMMENDED ROUTE:\nShip from {query.origin or 'origin'} to {port}, then clear through licensed agents and move inland by truck.\n\n"
        "ALTERNATIVE ROUTES:\n"
        "- Compare Tin Can Island for Lagos-bound cargo.\n"
        "- Compare Cotonou/Tema only after confirming cross-border costs, documentation, and transit risk.\n\n"
        f"ESTIMATED TIMELINE: {live_data.shipping_transit_days or '20-40'} days ocean transit plus clearance time.\n"
        f"FREIGHT ESTIMATE: USD {live_data.shipping_min}-{live_data.shipping_max} per container (estimated).\n"
        "INCOTERMS: Prefer FOB or FCA with independent freight control unless supplier CIF quote is independently benchmarked."
    )
    return AgentOutput(
        agent_name="Route and Logistics Agent (Local Fallback)",
        analysis=analysis,
        confidence=confidence,
        assumptions=[
            "Route plan uses static lane estimates because live Azure/Foundry routing analysis is unavailable.",
            "Transit excludes customs clearance and last-mile delivery unless separately quoted.",
        ],
        flags=["LOCAL_FALLBACK", "FREIGHT_COST_ESTIMATED"],
        risk_items=risks,
        key_findings=[
            f"Benchmark freight to {port} with at least two forwarders.",
            "Confirm port-specific documentation and terminal handling costs before shipment.",
        ],
    )


def risk_compliance(query: TradeQuery, live_data: LiveDataContext, market_intel_analysis: str, route_analysis: str) -> AgentOutput:
    flags = _product_flags(query.product)
    requirements = [
        "Confirm HS code, duty rate, VAT, levy exposure, and Form M/PAAR process with a licensed Nigerian customs broker.",
        "Verify supplier registration, pro-forma invoice, packing list, bill of lading, and certificate of origin requirements.",
    ]
    risks = [
        "Incorrect HS classification can cause duty underpayment, seizure risk, penalties, or clearance delays.",
        "Supplier fraud/counterfeit risk requires pre-shipment inspection and payment controls.",
        "FX availability and payment documentation can delay settlement and import processing.",
    ]
    if flags["electronics"]:
        requirements.append("Electronics may require SONCAP and, for communications devices, possible NCC type approval verification.")
        risks.append("SONCAP/NCC applicability must be verified before goods leave origin.")
    if flags["regulated_food_drug"]:
        requirements.append("Food, drug, cosmetics, or medical goods may require NAFDAC registration/permits.")
        risks.append("NAFDAC-regulated products can be blocked if registration is incomplete.")
    if query.disruption_context:
        risks.insert(0, f"Disruption signal requires immediate re-validation: {query.disruption_context}")

    confidence = ConfidenceLevel.LOW if flags["electronics"] or flags["regulated_food_drug"] or query.disruption_context else ConfidenceLevel.MEDIUM
    analysis = (
        "COMPLIANCE REQUIREMENTS:\n" + "\n".join(f"- {item}" for item in requirements) +
        "\n\nCRITICAL RISKS:\n" + "\n".join(f"- {risk}" for risk in risks) +
        "\n\nMITIGATION ACTIONS:\n"
        "- Obtain written HS-code/duty opinion before payment.\n"
        "- Verify SON/NAFDAC/NCC applicability directly with the regulator or accredited agents.\n"
        "- Use inspection, escrow/LC controls, and supplier due diligence for first-time suppliers."
    )
    return AgentOutput(
        agent_name="Risk and Compliance Agent (Local Fallback)",
        analysis=analysis,
        confidence=confidence,
        assumptions=[
            "Regulatory assessment is conservative and must be verified with SON, NAFDAC, NCC, and Nigeria Customs.",
            "Product classification was inferred from the query text only.",
        ],
        flags=["LOCAL_FALLBACK", "REGULATORY_VERIFICATION_REQUIRED"],
        risk_items=risks,
        key_findings=requirements,
    )


def critic(query: TradeQuery, live_data: LiveDataContext, market_intel: AgentOutput, route_logistics: AgentOutput, risk_compliance: AgentOutput):
    all_risks = market_intel.risk_items + route_logistics.risk_items + risk_compliance.risk_items
    blockers = [risk for risk in all_risks if any(term in risk.lower() for term in ["disruption", "blocked", "seizure", "soncap", "nafdac", "ncc"])]
    data_gaps = [
        "Supplier price and payment terms are not verified.",
        "HS code, duty rate, and regulator applicability need external confirmation.",
        "Freight and destination charges are estimates, not booked quotes.",
    ]
    if query.disruption_context:
        recommendation = TradeRecommendation.PAUSE_AND_INVESTIGATE
        confidence = ConfidenceLevel.LOW
        score = 45
    elif blockers:
        recommendation = TradeRecommendation.PROCEED_WITH_CAUTION
        confidence = ConfidenceLevel.MEDIUM
        score = 62
    else:
        recommendation = TradeRecommendation.PROCEED_WITH_CAUTION
        confidence = ConfidenceLevel.MEDIUM
        score = 68

    final_verdict = (
        f"{recommendation.value}: The trade may be viable, but proceed only after resolving compliance, landed-cost, "
        "supplier, and freight quote gaps."
    )
    analysis = (
        "EXECUTIVE SUMMARY:\n"
        "Local critic fallback found no basis for an unconditional proceed decision because key trade inputs remain unverified.\n\n"
        "AGENT DISAGREEMENTS:\n- None material in fallback mode; all agents recommend verification before commitment.\n\n"
        "CONTRADICTIONS:\n" + ("\n".join(f"- {risk}" for risk in blockers[:3]) if blockers else "- No direct contradictions detected.") +
        f"\n\nEVIDENCE QUALITY: MEDIUM\nCONFIDENCE: {confidence.value} ({score}/100)\n"
        "RATIONALE: Live/estimated operational data is available, but regulatory and price evidence requires third-party verification.\n\n"
        "CONFIDENCE LEDGER:\n"
        "  Raises confidence: live FX data, explicit freight estimate, conservative compliance checks\n"
        "  Lowers confidence: unverified HS code, estimated shipping, optional Azure agents unavailable\n\n"
        f"FINAL RECOMMENDATION: {recommendation.value}\n"
        "RATIONALE: Manageable only after confirming costs, documents, and regulatory approvals.\n\n"
        "TOP THREE ACTIONS:\n"
        "1. Get a licensed broker's landed-cost worksheet by HS code.\n"
        "2. Confirm SONCAP/NCC/NAFDAC applicability before supplier payment.\n"
        "3. Obtain written freight and clearance quotes with transit/port assumptions."
    )
    output = AgentOutput(
        agent_name="Critic and Verifier Agent (Local Fallback)",
        analysis=analysis,
        confidence=confidence,
        assumptions=["Azure AI Agents service unavailable; final verdict produced by deterministic fallback rules."],
        flags=["LOCAL_FALLBACK", "FINAL_VERDICT", "CONFIDENCE_LEDGER", "AGENT_DISAGREEMENT_DETECTION"],
        risk_items=blockers,
        key_findings=[
            "Get broker landed-cost worksheet.",
            "Verify regulator applicability.",
            "Benchmark freight and clearance quotes.",
        ],
    )
    ledger = {
        "score": score,
        "raises_confidence": ["Live FX data", "Explicit freight estimate", "Conservative compliance checks"],
        "lowers_confidence": data_gaps,
    }
    return output, recommendation, final_verdict, [], ledger
