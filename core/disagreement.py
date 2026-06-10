import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import AgentOutput, ConfidenceLevel

def analyze_disagreements(market_intel: AgentOutput, route_logistics: AgentOutput, risk_compliance: AgentOutput) -> dict:
    disagreements = []
    agreements = []
    resolution_required = []

    mi_conf = market_intel.confidence
    rl_conf = route_logistics.confidence
    rc_conf = risk_compliance.confidence

    confidence_values = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    mi_val = confidence_values.get(str(mi_conf.value if hasattr(mi_conf, 'value') else mi_conf), 2)
    rl_val = confidence_values.get(str(rl_conf.value if hasattr(rl_conf, 'value') else rl_conf), 2)
    rc_val = confidence_values.get(str(rc_conf.value if hasattr(rc_conf, 'value') else rc_conf), 2)

    if abs(mi_val - rc_val) >= 2:
        disagreements.append({
            "agents": ["Market Intelligence", "Risk & Compliance"],
            "type": "CONFIDENCE_CONFLICT",
            "detail": f"Market Intel rates confidence {mi_conf} but Risk & Compliance rates {rc_conf}. This gap suggests the financial opportunity may conflict with regulatory risk.",
            "severity": "HIGH",
            "resolution": "Trader must resolve regulatory uncertainty before committing capital."
        })

    if abs(rl_val - rc_val) >= 2:
        disagreements.append({
            "agents": ["Route & Logistics", "Risk & Compliance"],
            "type": "LOGISTICS_RISK_CONFLICT",
            "detail": f"Logistics Agent rates confidence {rl_conf} but Risk Agent rates {rc_conf}. Route may be logistically viable but regulatory compliance is uncertain.",
            "severity": "HIGH",
            "resolution": "Verify compliance requirements before finalizing logistics plan."
        })

    if abs(mi_val - rl_val) >= 2:
        disagreements.append({
            "agents": ["Market Intelligence", "Route & Logistics"],
            "type": "COST_ROUTE_CONFLICT",
            "detail": f"Market Intel rates confidence {mi_conf} but Logistics rates {rl_conf}. Financial viability assessment conflicts with logistics feasibility.",
            "severity": "MEDIUM",
            "resolution": "Get live freight quotes to reconcile cost estimates."
        })

    mi_risks = set([r.lower()[:30] for r in market_intel.risk_items])
    rl_risks = set([r.lower()[:30] for r in route_logistics.risk_items])
    rc_risks = set([r.lower()[:30] for r in risk_compliance.risk_items])

    overlapping_risks = []
    all_risk_texts = list(market_intel.risk_items) + list(route_logistics.risk_items) + list(risk_compliance.risk_items)
    fx_risks = [r for r in all_risk_texts if any(k in r.lower() for k in ["fx", "naira", "exchange", "currency"])]
    if len(fx_risks) >= 2:
        agreements.append("All agents independently flagged FX/currency risk — HIGH CONFIDENCE this is a critical risk")

    port_risks = [r for r in all_risk_texts if any(k in r.lower() for k in ["port", "apapa", "congestion", "delay"])]
    if len(port_risks) >= 2:
        agreements.append("Multiple agents flagged port congestion risk — HIGH CONFIDENCE this requires mitigation")

    compliance_risks = [r for r in all_risk_texts if any(k in r.lower() for k in ["soncap", "ncc", "nafdac", "certification"])]
    if len(compliance_risks) >= 2:
        agreements.append("Multiple agents flagged certification requirements — HIGH CONFIDENCE SONCAP/NCC verification is mandatory")

    if disagreements:
        resolution_required = [d["resolution"] for d in disagreements]

    overall_conflict_level = "NONE"
    if any(d["severity"] == "HIGH" for d in disagreements):
        overall_conflict_level = "HIGH"
    elif disagreements:
        overall_conflict_level = "MEDIUM"

    return {
        "disagreements": disagreements,
        "agreements": agreements,
        "resolution_required": resolution_required,
        "conflict_level": overall_conflict_level,
        "disagreement_count": len(disagreements),
        "agreement_count": len(agreements),
        "verdict": "CONTRADICTIONS REQUIRE RESOLUTION BEFORE PROCEEDING" if disagreements else "AGENTS IN AGREEMENT — RECOMMENDATION IS CONSISTENT"
    }

def print_disagreement_report(analysis: dict):
    print("\n" + "="*60)
    print("AGENT INTELLIGENCE DISAGREEMENT REPORT")
    print("="*60)
    print(f"Conflict Level: {analysis['conflict_level']}")
    print(f"Disagreements: {analysis['disagreement_count']} | Agreements: {analysis['agreement_count']}")
    print(f"\nVERDICT: {analysis['verdict']}")

    if analysis['disagreements']:
        print("\n⚠️  CONTRADICTIONS DETECTED:")
        for i, d in enumerate(analysis['disagreements'], 1):
            print(f"\n  [{i}] {d['type']} (Severity: {d['severity']})")
            print(f"  Agents: {' vs '.join(d['agents'])}")
            print(f"  Issue: {d['detail']}")
            print(f"  Resolution Required: {d['resolution']}")

    if analysis['agreements']:
        print("\n✅ CROSS-AGENT AGREEMENTS (HIGH CONFIDENCE):")
        for a in analysis['agreements']:
            print(f"  • {a}")

    if analysis['resolution_required']:
        print("\n🔴 TRADER MUST RESOLVE BEFORE PROCEEDING:")
        for i, r in enumerate(analysis['resolution_required'], 1):
            print(f"  {i}. {r}")
    print("="*60)
