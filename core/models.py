from dataclasses import dataclass, field
from typing import List

@dataclass
class TradeQuery:
    raw: str
    product: str = ""
    quantity: int = 0
    origin: str = ""
    destination: str = ""

@dataclass
class AgentOutput:
    agent_name: str
    analysis: str
    confidence: str  # HIGH / MEDIUM / LOW
    assumptions: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)

@dataclass
class TradeBrief:
    query: TradeQuery
    market_intel: AgentOutput = None
    route_logistics: AgentOutput = None
    risk_compliance: AgentOutput = None
    critic_verdict: AgentOutput = None
    final_recommendation: str = ""
