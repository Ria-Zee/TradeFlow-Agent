from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class TradeRecommendation(str, Enum):
    PROCEED = "PROCEED"
    PROCEED_WITH_CAUTION = "PROCEED WITH CAUTION"
    PAUSE_AND_INVESTIGATE = "PAUSE AND INVESTIGATE"

@dataclass
class TradeQuery:
    raw: str
    product: str = ""
    quantity: int = 0
    origin: str = ""
    destination: str = ""
    disruption_context: str = ""

@dataclass
class LiveDataContext:
    usd_ngn_rate: Optional[float] = None
    usd_cny_rate: Optional[float] = None
    cny_ngn_rate: Optional[float] = None
    shipping_min: Optional[int] = None
    shipping_max: Optional[int] = None
    shipping_transit_days: Optional[str] = None
    data_timestamp: str = ""
    data_quality: str = "LIVE_FX + ESTIMATED_SHIPPING"

@dataclass
class AgentOutput:
    agent_name: str
    analysis: str
    confidence: ConfidenceLevel
    assumptions: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    risk_items: List[str] = field(default_factory=list)
    key_findings: List[str] = field(default_factory=list)

@dataclass
class TradeBrief:
    query: TradeQuery
    live_data: Optional[LiveDataContext] = None
    market_intel: Optional[AgentOutput] = None
    route_logistics: Optional[AgentOutput] = None
    risk_compliance: Optional[AgentOutput] = None
    critic_verdict: Optional[AgentOutput] = None
    final_recommendation: TradeRecommendation = TradeRecommendation.PAUSE_AND_INVESTIGATE
    final_verdict: str = ""
    agent_disagreements: List[str] = field(default_factory=list)
    confidence_ledger: dict = field(default_factory=dict)
