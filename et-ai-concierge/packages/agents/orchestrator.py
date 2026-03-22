"""
ET AI Concierge — LangGraph Orchestrator (Agent 0)
Main brain: receives all messages, routes to workers, synthesizes responses.
Serves as the FastAPI application entry point.
"""
import json
import uuid
import asyncio
import datetime
from typing import Optional, Dict, Any, AsyncGenerator
from pydantic import BaseModel as PydanticBaseModel

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from auth import AuthUser, get_current_user, get_optional_user

from state import (
    ConciergeState, UserProfile, Message, ChatRequest, ChatResponse,
    SessionState, AgentResponse, SentimentType, IntentType, ModalityType,
    OnboardingRequest, OnboardingResponse,
)
from config import settings
from compliance_wrapper import compliance_wrapper
from profiling_agent import (
    run_profiling_agent, get_onboarding_step, process_onboarding_answer,
    complete_profiling, PROFILING_QUESTIONS, calculate_profile_completeness,
    run_xray_step, extract_xray_profile, map_xray_to_persona,
    XRAY_WARM_OPEN, XRAY_FALLBACK_QUESTIONS, PERSONA_MAPPING,
)
from editorial_agent import run_editorial_agent
from market_intelligence_agent import run_market_intelligence_agent
from marketplace_agent import run_marketplace_agent, fetch_mock_elss_funds, fetch_mock_insurance_quotes
from intent_router import detect_upsell_intent
from behavioral_monitor import run_behavioral_monitor, track_paywall_hit, track_query
from database import (
    init_db, create_user, update_user_profile, get_user, log_audit,
    save_chat_message, get_chat_history,
)

# ─── Optional: Groq LLM ──────────────────────────────────────────────────────
try:
    from groq import Groq
    groq_client = Groq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None
except ImportError:
    groq_client = None

# ─── Optional: Redis ──────────────────────────────────────────────────────────
try:
    import redis as redis_lib
    redis_client = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
    print("✅ Redis connected")
except Exception:
    redis_client = None
    print("⚠️ Redis not available, using in-memory session store")

# ─── In-Memory Fallbacks ─────────────────────────────────────────────────────
_sessions: Dict[str, SessionState] = {}
_profiles: Dict[str, UserProfile] = {}
_onboarding_state: Dict[str, Dict[str, Any]] = {}


# ─── FastAPI App ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are the ET AI Concierge — a Financial Life Navigator for The Economic Times ecosystem.
Your job is not to answer questions. Your job is to understand the user's complete financial life
and proactively guide them toward the ET tools, stories, courses, and financial products that
will genuinely help them.

Every message you receive, do three things before responding:
1. Check the user's stored profile (goals, risk tolerance, interests, persona).
2. Detect sentiment: frustrated / anxious / curious / confident.
3. Detect intent: inform / transact / learn / discover.

Then route to the right worker agent. Never answer from your own knowledge alone.
Always ground your response in real ET content or real market data.

When you synthesize the final response:
- Be conversational, not corporate.
- Never give generic advice. Always cite a specific ET tool, story, or product.
- If the user seems anxious, lower jargon density and increase reassurance.
- If the user is an active trader, be precise and data-dense."""

app = FastAPI(
    title="ET AI Concierge API",
    description="Multi-Agent Financial Life Navigator",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_db()
    print("🚀 ET AI Concierge API is running")


# ─── Helper Functions ─────────────────────────────────────────────────────────

def _get_profile(user_id: str) -> UserProfile:
    """Get or create user profile."""
    if user_id in _profiles:
        return _profiles[user_id]
    profile = UserProfile(id=user_id)
    _profiles[user_id] = profile
    return profile


def _save_session(user_id: str, session: SessionState):
    """Save session to Redis or in-memory."""
    session.last_interaction = datetime.datetime.utcnow().isoformat()
    data = session.model_dump_json()
    if redis_client:
        try:
            redis_client.setex(f"session:{user_id}:latest", 3600, data)
            return
        except Exception:
            pass
    _sessions[user_id] = session


def _get_session(user_id: str) -> Optional[SessionState]:
    """Retrieve session from Redis or in-memory."""
    if redis_client:
        try:
            data = redis_client.get(f"session:{user_id}:latest")
            if data:
                return SessionState(**json.loads(data))
        except Exception:
            pass
    return _sessions.get(user_id)


def detect_sentiment(message: str) -> SentimentType:
    """Simple rule-based sentiment detection. Replaced by LLM in production."""
    msg = message.lower()
    if any(w in msg for w in ["worried", "scared", "afraid", "panic", "crash", "loss"]):
        return SentimentType.ANXIOUS
    elif any(w in msg for w in ["frustrated", "annoyed", "angry", "confused", "stuck"]):
        return SentimentType.FRUSTRATED
    elif any(w in msg for w in ["sure", "confident", "great", "profit", "rally"]):
        return SentimentType.CONFIDENT
    return SentimentType.CURIOUS


def detect_intent(message: str) -> IntentType:
    """Simple rule-based intent detection."""
    msg = message.lower()
    if any(w in msg for w in ["buy", "sell", "apply", "transfer", "invest", "loan"]):
        return IntentType.TRANSACT
    elif any(w in msg for w in ["learn", "course", "masterclass", "understand", "explain", "how"]):
        return IntentType.LEARN
    elif any(w in msg for w in ["what", "which", "tell me", "news", "article", "read"]):
        return IntentType.INFORM
    return IntentType.DISCOVER


def route_to_agent(message: str, intent: IntentType, profile: UserProfile) -> str:
    """Determine which agent should handle this message."""
    msg = message.lower()

    # Profile incomplete → profiling agent
    if not profile.onboarding_complete and calculate_profile_completeness({}) < 0.6:
        if any(w in msg for w in ["start", "hello", "hi", "new", "first"]):
            return "profiling_agent"

    # Market data queries → market intelligence
    if any(w in msg for w in [
        "price", "nifty", "sensex", "gold", "stock", "market",
        "portfolio", "rebalance", "nav", "mutual fund", "briefing", "morning"
    ]):
        return "market_intelligence_agent"

    # Financial product queries → marketplace
    if any(w in msg for w in [
        "loan", "emi", "home loan", "credit card", "insurance", "fd",
        "fixed deposit", "nps", "pension", "apply"
    ]):
        return "marketplace_agent"

    # Editorial / learning queries → editorial
    if any(w in msg for w in [
        "article", "news", "read", "et prime", "analysis",
        "learn", "course", "masterclass"
    ]):
        return "editorial_agent"

    # Intent-based fallback
    if intent == IntentType.TRANSACT:
        return "marketplace_agent"
    elif intent == IntentType.LEARN:
        return "editorial_agent"
    elif intent == IntentType.INFORM:
        return "editorial_agent"

    return "editorial_agent"  # Default to editorial


def _llm_synthesize(agent_response: AgentResponse, sentiment: SentimentType, user_message: str, upsell_data: str = None) -> str:
    """Use Groq LLM to add a conversational wrapper around the agent response."""
    if not groq_client:
        return agent_response.content

    try:
        tone_instruction = ""
        if sentiment == SentimentType.ANXIOUS:
            tone_instruction = "The user seems anxious. Use reassuring, simple language. Avoid jargon."
        elif sentiment == SentimentType.FRUSTRATED:
            tone_instruction = "The user seems frustrated. Be empathetic and direct."
        elif sentiment == SentimentType.CONFIDENT:
            tone_instruction = "The user is confident. Be precise and data-focused."
            
        system_content = f"{SYSTEM_PROMPT}\n\n{tone_instruction}"
        
        synthesis_instruction = "Now synthesize this into a conversational, helpful response. Keep the data and links intact."
        if upsell_data:
            synthesis_instruction += (
                "\n\nYou have additionally detected a cross-sell opportunity based on the user's intent. "
                "Seamlessly weave this recommendation naturally into the end of your answer. "
                "CRITICAL: Do NOT output raw JSON, lists of dictionaries, or code formatting. Present the partner data "
                "as a naturally written list or table within your conversational response. "
                f"Partner Data:\n{upsell_data}"
            )

        response = groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": f"Here's the data from our systems:\n{agent_response.content}"},
                {"role": "user", "content": synthesis_instruction},
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"⚠️ LLM synthesis failed: {e}")
        return agent_response.content


# ─── API Endpoints ────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "services": {
            "redis": redis_client is not None,
            "groq_llm": groq_client is not None,
        }
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, auth_user: AuthUser = Depends(get_current_user)):
    """Main chat endpoint. Routes to the appropriate agent."""
    user_id = auth_user.user_id
    session_id = request.session_id or str(uuid.uuid4())
    profile = _get_profile(user_id)

    # Detect sentiment and intent
    sentiment = detect_sentiment(request.message)
    intent = detect_intent(request.message)

    # Route to agent
    agent_name = route_to_agent(request.message, intent, profile)

    # Execute agent
    if agent_name == "profiling_agent":
        agent_response = run_profiling_agent(request.message, profile)
    elif agent_name == "editorial_agent":
        agent_response = run_editorial_agent(request.message, profile)
    elif agent_name == "market_intelligence_agent":
        agent_response = run_market_intelligence_agent(request.message, profile)
    elif agent_name == "marketplace_agent":
        agent_response = run_marketplace_agent(request.message, profile)
    else:
        agent_response = run_editorial_agent(request.message, profile)

    # Detect upsell intent (Phase 3)
    upsell_intent = detect_upsell_intent(request.message, profile)
    upsell_data = None
    if upsell_intent.get("trigger_active") and upsell_intent.get("trigger_type"):
        trigger_type = upsell_intent["trigger_type"]
        if trigger_type == "tax_marketplace":
            mock_data = fetch_mock_elss_funds()
            upsell_data = f"Top ELSS Funds: {json.dumps(mock_data)}"
        elif trigger_type == "insurance_marketplace":
            mock_data = fetch_mock_insurance_quotes()
            upsell_data = f"Top Insurance Quotes: {json.dumps(mock_data)}"

    # Check behavioral triggers
    behavioral_response = run_behavioral_monitor(user_id, request.message)

    # Apply compliance wrapper
    agent_response = compliance_wrapper.wrap(agent_response, profile, session_id, intent.value)

    # LLM synthesis (if available)
    final_content = _llm_synthesize(agent_response, sentiment, request.message, upsell_data=upsell_data)

    # Append behavioral nudge if any
    if behavioral_response:
        final_content += f"\n\n---\n{behavioral_response.content}"

    # Add disclaimers
    for disclaimer in agent_response.disclaimers:
        if disclaimer not in final_content:
            final_content += f"\n\n⚠️ *{disclaimer}*"

    # Update session
    session = _get_session(user_id) or SessionState(
        user_id=user_id,
        session_id=session_id,
        modality=request.modality,
    )
    session.conversation_history.append(Message(role="user", content=request.message))
    session.conversation_history.append(Message(role="assistant", content=final_content, agent_id=agent_name))
    _save_session(user_id, session)

    # Persist to chat_history DB
    save_chat_message(user_id, session_id, "user", request.message)
    save_chat_message(user_id, session_id, "assistant", final_content, agent_id=agent_name)

    return ChatResponse(
        message=final_content,
        session_id=session_id,
        agent_used=agent_name,
        recommendations=agent_response.recommendations,
        disclaimers=agent_response.disclaimers,
    )


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest, auth_user: AuthUser = Depends(get_current_user)):
    """SSE streaming endpoint for the chat UI."""
    async def generate() -> AsyncGenerator[str, None]:
        # Get the full response first
        response = await chat(request, auth_user=auth_user)
        # Stream it token-by-token
        words = response.message.split(" ")
        for i, word in enumerate(words):
            yield f"data: {json.dumps({'token': word + ' ', 'done': False})}\n\n"
            await asyncio.sleep(0.03)
        yield f"data: {json.dumps({'token': '', 'done': True, 'agent_used': response.agent_used})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/session/resume")
async def resume_session(modality: str = "web", auth_user: AuthUser = Depends(get_current_user)):
    """Resume a session from another modality (voice → web handoff)."""
    user_id = auth_user.user_id
    session = _get_session(user_id)

    if session:
        time_gap = session.minutes_since_last_interaction
        last_messages = session.conversation_history[-3:] if session.conversation_history else []

        # Generate transition message
        if last_messages:
            last_topic = last_messages[-1].content[:100]
            transition_msg = (
                f"Welcome back! You were asking about this earlier: \"{last_topic}...\" "
                f"I've kept all the context from your {session.modality.value} session. "
                f"Let's continue right where you left off."
            )
        else:
            transition_msg = "Welcome back! Let's pick up where we left off."

        return {
            "session": session.model_dump(),
            "transition_message": transition_msg,
            "time_gap_minutes": round(time_gap, 1),
        }

    profile = _get_profile(user_id)
    return {
        "profile": profile.model_dump() if profile else None,
        "is_new_session": True,
        "transition_message": "Welcome to ET AI Concierge! I'm your Financial Life Navigator.",
    }


# ─── Onboarding Endpoints ────────────────────────────────────────────────────

@app.get("/api/onboarding/start")
async def start_onboarding(auth_user: AuthUser = Depends(get_current_user)):
    """Start the onboarding flow."""
    user_id = auth_user.user_id
    _onboarding_state[user_id] = {"step": 0, "answers": {}}
    return get_onboarding_step(0).model_dump()


@app.post("/api/onboarding/answer")
async def answer_onboarding(request: OnboardingRequest, auth_user: AuthUser = Depends(get_current_user)):
    """Submit an onboarding answer."""
    user_id = request.user_id
    state = _onboarding_state.get(user_id, {"step": 0, "answers": {}})

    # Process the answer
    state["answers"] = process_onboarding_answer(request.step, request.answer, state["answers"])
    next_step = request.step + 1
    state["step"] = next_step
    _onboarding_state[user_id] = state

    # Check if complete
    if next_step > len(PROFILING_QUESTIONS):
        result = complete_profiling(state["answers"])

        # Update profile
        profile = _get_profile(user_id)
        profile.persona = result["persona"]
        profile.onboarding_complete = True
        profile.risk_score = state["answers"].get("risk_score", 5)
        profile.interests = state["answers"].get("interests", [])
        profile.primary_goal = state["answers"].get("primary_goal")
        profile.income_type = state["answers"].get("income_type")
        profile.age_group = state["answers"].get("age_group")
        profile.profile_completeness = result["profile_completeness"]
        _profiles[user_id] = profile

        # Save to Postgres
        update_user_profile(user_id, profile.model_dump())

        return OnboardingResponse(
            step=next_step,
            is_complete=True,
            persona=result["persona"],
            recommended_tools=result["recommended_tools"],
        ).model_dump()

    return get_onboarding_step(next_step).model_dump()


# ─── Financial X-Ray Endpoints ────────────────────────────────────────────────

_xray_conversations: Dict[str, list] = {}  # user_id -> conversation history
_xray_question_count: Dict[str, int] = {}  # user_id -> question number


class XRayRequest(PydanticBaseModel):
    user_id: str = "default_user"
    message: str
    session_id: Optional[str] = None


@app.post("/api/chat/xray")
async def chat_xray(request: XRayRequest, auth_user: AuthUser = Depends(get_current_user)):
    """Financial X-Ray endpoint — LLM-driven 5-question onboarding via chat."""
    user_id = auth_user.user_id
    session_id = request.session_id or str(uuid.uuid4())
    profile = _get_profile(user_id)

    # If already onboarded, return profile summary
    if profile.onboarding_complete:
        persona = profile.persona
        mapping = PERSONA_MAPPING.get(persona, {})
        tools = mapping.get("primary_tools", [])
        return {
            "message": f"Your Financial X-Ray is already complete! You're mapped as a **{persona.value if hasattr(persona, 'value') else persona}**. Your recommended tools: {', '.join(tools)}.",
            "is_complete": True,
            "persona": persona.value if hasattr(persona, 'value') else persona,
            "session_id": session_id,
        }

    # Force reset if user hits refresh and sends an empty initialization message
    if not request.message:
        _xray_conversations[user_id] = []
        _xray_question_count[user_id] = 0

    conv = _xray_conversations[user_id]
    q_num = _xray_question_count[user_id]

    # First call — generate warm open + first question
    if not conv and not request.message:
        first_q = run_xray_step([], 0)
        greeting = XRAY_WARM_OPEN + first_q
        conv.append({"role": "assistant", "content": greeting})
        _xray_conversations[user_id] = conv

        save_chat_message(user_id, session_id, "assistant", greeting, agent_id="profiling_agent")

        return {
            "message": greeting,
            "is_complete": False,
            "question_number": 0,
            "session_id": session_id,
        }

    # User answered — add to conversation
    conv.append({"role": "user", "content": request.message})
    q_num += 1
    _xray_question_count[user_id] = q_num

    save_chat_message(user_id, session_id, "user", request.message)

    # Generate next question via LLM
    next_response = run_xray_step(conv, q_num)
    conv.append({"role": "assistant", "content": next_response})
    _xray_conversations[user_id] = conv

    save_chat_message(user_id, session_id, "assistant", next_response, agent_id="profiling_agent")

    # Check if the X-Ray is complete (LLM includes JSON block)
    extracted = extract_xray_profile(next_response)
    if extracted:
        persona_str = map_xray_to_persona(extracted)
        mapping = PERSONA_MAPPING.get(persona_str, {})
        tools = []
        for k, v in PERSONA_MAPPING.items():
            key_val = k.value if hasattr(k, 'value') else k
            if key_val == persona_str:
                tools = v.get("primary_tools", [])
                break

        # Update profile
        profile.persona = persona_str
        profile.onboarding_complete = True
        profile.risk_score = extracted.get("risk_score", 5)
        profile.interests = extracted.get("interests", [])
        profile.primary_goal = extracted.get("primary_goal")
        profile.income_type = extracted.get("income_type")
        profile.age_group = extracted.get("age_group")
        profile.profile_completeness = 1.0
        _profiles[user_id] = profile

        # Save to DB
        update_user_profile(user_id, profile.model_dump())

        # Cleanup
        del _xray_conversations[user_id]
        del _xray_question_count[user_id]

        return {
            "message": next_response,
            "is_complete": True,
            "persona": persona_str,
            "recommended_tools": tools,
            "session_id": session_id,
        }

    return {
        "message": next_response,
        "is_complete": False,
        "question_number": q_num,
        "session_id": session_id,
    }


@app.get("/api/chat/history")
async def chat_history(session_id: Optional[str] = None, limit: int = 50, auth_user: AuthUser = Depends(get_current_user)):
    """Retrieve chat history for a user."""
    user_id = auth_user.user_id
    messages = get_chat_history(user_id, session_id, limit)
    # Serialize datetime objects
    for m in messages:
        for k, v in m.items():
            if hasattr(v, 'isoformat'):
                m[k] = v.isoformat()
        if 'id' in m:
            m['id'] = str(m['id'])
    return {"messages": messages, "count": len(messages)}


# ─── Behavioral Tracking Endpoints ───────────────────────────────────────────

@app.post("/api/track/paywall")
async def track_paywall(auth_user: AuthUser = Depends(get_current_user)):
    """Track a paywall hit."""
    user_id = auth_user.user_id
    track_paywall_hit(user_id)
    behavioral = run_behavioral_monitor(user_id, "")
    if behavioral:
        return {"triggered": True, "message": behavioral.content, "recommendations": [r.model_dump() for r in behavioral.recommendations]}
    return {"triggered": False}


@app.get("/api/profile")
async def get_profile(auth_user: AuthUser = Depends(get_current_user)):
    """Get user profile."""
    profile = _get_profile(auth_user.user_id)
    return profile.model_dump()


# ─── Public Auth Endpoints ───────────────────────────────────────────────────

class RegisterRequest(PydanticBaseModel):
    email: str
    name: Optional[str] = None
    password: Optional[str] = None
    provider: str = "credentials"


class VerifyRequest(PydanticBaseModel):
    email: str
    password: str


@app.post("/api/auth/register")
async def register_user(request: RegisterRequest):
    """Register a new user. Called by NextAuth on first sign-in."""
    from database import create_or_get_user
    user = create_or_get_user(
        email=request.email,
        name=request.name,
        password=request.password,
        provider=request.provider,
    )
    if user:
        return {"id": str(user["id"]), "email": user.get("email"), "name": user.get("name")}
    raise HTTPException(status_code=400, detail="Could not create user")


@app.post("/api/auth/verify")
async def verify_credentials(request: VerifyRequest):
    """Verify email/password for NextAuth Credentials provider."""
    from database import verify_user_credentials
    user = verify_user_credentials(request.email, request.password)
    if user:
        return {"id": str(user["id"]), "email": user.get("email"), "name": user.get("name")}
    raise HTTPException(status_code=401, detail="Invalid email or password")


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("orchestrator:app", host="0.0.0.0", port=8000, reload=True)
