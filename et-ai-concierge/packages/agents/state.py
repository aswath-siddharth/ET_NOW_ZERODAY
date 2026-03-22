"""
ET AI Concierge — State Models
All Pydantic models for the multi-agent system state.
"""
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum
import datetime
import uuid


# ─── Enums ────────────────────────────────────────────────────────────────────

class PersonaType(str, Enum):
    CONSERVATIVE_SAVER = "PERSONA_CONSERVATIVE_SAVER"
    ACTIVE_TRADER = "PERSONA_ACTIVE_TRADER"
    YOUNG_PROFESSIONAL = "PERSONA_YOUNG_PROFESSIONAL"
    CORPORATE_EXECUTIVE = "PERSONA_CORPORATE_EXECUTIVE"
    HOME_BUYER = "PERSONA_HOME_BUYER"


class SentimentType(str, Enum):
    FRUSTRATED = "frustrated"
    ANXIOUS = "anxious"
    CURIOUS = "curious"
    CONFIDENT = "confident"


class IntentType(str, Enum):
    INFORM = "inform"
    TRANSACT = "transact"
    LEARN = "learn"
    DISCOVER = "discover"


class ModalityType(str, Enum):
    VOICE = "voice"
    WEB = "web"
    MOBILE = "mobile"


# ─── Core Models ──────────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    agent_id: Optional[str] = None


class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    persona: Optional[PersonaType] = None
    risk_score: Optional[int] = None  # 1–10
    interests: List[str] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)
    income_type: Optional[str] = None  # salaried / self-employed / business
    age_group: Optional[str] = None  # 20s, 30s, 40s, 50+
    has_emergency_fund: Optional[bool] = None
    home_ownership: Optional[str] = None  # renting / owning
    investment_horizon: Optional[str] = None  # short-term / long-term
    is_active_trader: Optional[bool] = None
    primary_goal: Optional[str] = None  # saving / growing / protecting / buying
    has_tax_investments: Optional[bool] = False
    has_insurance: Optional[bool] = False
    onboarding_complete: bool = False
    has_et_prime_subscription: bool = False
    profile_completeness: float = 0.0


class Recommendation(BaseModel):
    type: str  # "article", "tool", "product", "course"
    title: str
    description: str
    deeplink: Optional[str] = None
    source_agent: str
    confidence: float = 0.8


class ComplianceFlag(BaseModel):
    flag_type: str
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


# ─── Agent Response ───────────────────────────────────────────────────────────

class AgentResponse(BaseModel):
    agent_id: str
    content: str
    type: str = "general"  # general, investment_advice, loan_recommendation, etc.
    contains_investment_advice: bool = False
    recommendations: List[Recommendation] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    reasoning_trace: Optional[str] = None
    confidence_score: float = 0.8
    disclaimers: List[str] = Field(default_factory=list)

    def append_disclaimer(self, disclaimer: str):
        self.disclaimers.append(disclaimer)
        self.content += f"\n\n⚠️ *{disclaimer}*"


# ─── Concierge State (LangGraph) ─────────────────────────────────────────────

class ConciergeState(BaseModel):
    """Main state that flows through the LangGraph orchestrator."""
    user_id: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_history: List[Message] = Field(default_factory=list)
    user_profile: Optional[UserProfile] = None
    active_agents: List[str] = Field(default_factory=list)
    pending_recommendations: List[Recommendation] = Field(default_factory=list)
    modality_context: ModalityType = ModalityType.WEB
    compliance_flags: List[ComplianceFlag] = Field(default_factory=list)

    # Routing state
    current_message: str = ""
    detected_sentiment: Optional[SentimentType] = None
    detected_intent: Optional[IntentType] = None
    routed_agent: Optional[str] = None

    # Agent outputs
    agent_response: Optional[AgentResponse] = None
    final_response: Optional[str] = None

    # Profiling state
    profiling_step: int = 0
    profiling_answers: Dict[str, Any] = Field(default_factory=dict)


# ─── Session State (Redis) ───────────────────────────────────────────────────

class SessionState(BaseModel):
    """Stored in Redis for cross-modal session resume."""
    user_id: str
    session_id: str
    conversation_history: List[Message] = Field(default_factory=list)
    user_profile: Optional[UserProfile] = None
    modality: ModalityType = ModalityType.WEB
    last_interaction: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    active: bool = True

    @property
    def minutes_since_last_interaction(self) -> float:
        last = datetime.datetime.fromisoformat(self.last_interaction)
        now = datetime.datetime.utcnow()
        return (now - last).total_seconds() / 60


# ─── Behavioral Session ──────────────────────────────────────────────────────

class BehavioralSession(BaseModel):
    """Tracks user behavior signals for the Behavioral Monitor Agent."""
    user_id: str
    paywall_hits: int = 0
    page_views: Dict[str, int] = Field(default_factory=dict)
    time_on_page: Dict[str, float] = Field(default_factory=dict)
    has_used: Dict[str, bool] = Field(default_factory=dict)
    enrolled_in: Dict[str, bool] = Field(default_factory=dict)
    recent_queries: List[str] = Field(default_factory=list)
    days_since_product_signup: int = 0


# ─── API Request/Response Models ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = "default_user"
    modality: ModalityType = ModalityType.WEB


class ChatResponse(BaseModel):
    message: str
    session_id: str
    agent_used: Optional[str] = None
    recommendations: List[Recommendation] = Field(default_factory=list)
    disclaimers: List[str] = Field(default_factory=list)


class OnboardingRequest(BaseModel):
    user_id: str
    answer: str
    step: int


class OnboardingResponse(BaseModel):
    question: Optional[str] = None
    step: int
    is_complete: bool = False
    persona: Optional[str] = None
    recommended_tools: List[Dict[str, Any]] = Field(default_factory=list)
