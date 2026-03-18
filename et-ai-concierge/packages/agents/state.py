from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import datetime

class UserProfile(BaseModel):
    id: str
    persona: Optional[str] = None
    risk_score: Optional[int] = None
    interests: List[str] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)
    onboarding_complete: bool = False

class Message(BaseModel):
    role: str
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())

class ConciergeState(BaseModel):
    user_id: str
    session_id: str
    conversation_history: List[Message] = Field(default_factory=list)
    user_profile: Optional[UserProfile] = None
    active_agents: List[str] = Field(default_factory=list)
    modality_context: str = "web"
    compliance_flags: List[str] = Field(default_factory=list)
    
    # Track the next node to route to
    next_action: Optional[str] = None
    final_response: Optional[str] = None
