"""
ET AI Concierge — Profiling Agent (Agent 1)
Onboards new users via 9 questions, maps to one of 5 financial personas.
"""
import json
from typing import Dict, Any, Optional, List
from state import (
    UserProfile, PersonaType, AgentResponse, Recommendation,
    OnboardingResponse
)
from config import settings

# ─── Persona → Product Mapping ────────────────────────────────────────────────

PERSONA_MAPPING: Dict[str, Dict[str, Any]] = {
    PersonaType.CONSERVATIVE_SAVER: {
        "primary_tools": ["ET Wealth Edition", "NPS Calculator", "FD Rate Tracker"],
        "et_prime_sections": ["Personal Finance", "Tax Saving"],
        "masterclass": None,
        "marketplace_products": ["Fixed Deposits", "NPS", "Health Insurance"]
    },
    PersonaType.ACTIVE_TRADER: {
        "primary_tools": ["Alpha Trades", "Stock Reports Plus", "Candlestick Screener", "RSI Screener"],
        "et_prime_sections": ["Markets", "Tech", "Corporate Governance"],
        "masterclass": "Technical Analysis Masterclass",
        "marketplace_products": ["Demat Account", "Margin Loans"]
    },
    PersonaType.YOUNG_PROFESSIONAL: {
        "primary_tools": ["ET Wealth SIP Guide", "Young Mind Program", "AI for Business Leaders"],
        "et_prime_sections": ["Startups", "Tech", "Career"],
        "masterclass": "Young Mind Entrepreneurship Program",
        "marketplace_products": ["SIP platforms", "Term Insurance", "Credit Card"]
    },
    PersonaType.CORPORATE_EXECUTIVE: {
        "primary_tools": ["ET Prime", "Wealth Edition", "Today's ePaper"],
        "et_prime_sections": ["Corporate Governance", "Aviation", "Auto", "Pharma"],
        "masterclass": "Strategic Leadership Masterclass",
        "marketplace_products": ["Premium Credit Cards", "Portfolio Management Services"]
    },
    PersonaType.HOME_BUYER: {
        "primary_tools": ["Home Loan EMI Calculator", "Loan Marketplace", "RBI Rate Tracker"],
        "et_prime_sections": ["Real Estate", "Digital Real Estate", "Infrastructure"],
        "masterclass": "Build Passive Income with Mutual Funds",
        "marketplace_products": ["Home Loans (SBI, HDFC, Kotak)", "Home Insurance"]
    }
}

# ─── Profiling Questions ──────────────────────────────────────────────────────

PROFILING_QUESTIONS = [
    {
        "key": "income_type",
        "question": "Are you currently salaried, self-employed, or a business owner?",
        "options": ["salaried", "self-employed", "business owner"]
    },
    {
        "key": "age_group",
        "question": "Which age bracket are you in — 20s, 30s, 40s, or 50+?",
        "options": ["20s", "30s", "40s", "50+"]
    },
    {
        "key": "has_emergency_fund",
        "question": "Do you have 3–6 months of expenses saved as an emergency fund?",
        "options": ["yes", "no"]
    },
    {
        "key": "home_ownership",
        "question": "Are you currently renting, or do you own your home?",
        "options": ["renting", "owning"]
    },
    {
        "key": "risk_score",
        "question": "On a scale of 1 to 10, how comfortable are you with short-term portfolio losses in exchange for long-term growth?",
        "options": list(range(1, 11))
    },
    {
        "key": "interests",
        "question": "Which sectors do you follow most closely? For example — Tech, Pharma, Infrastructure, or Banking?",
        "options": ["Tech", "Pharma", "Infrastructure", "Banking", "Auto", "Real Estate", "FMCG"]
    },
    {
        "key": "investment_horizon",
        "question": "Are you primarily thinking about the next 1–3 years, or are you building wealth for 10+ years?",
        "options": ["1-3 years", "3-5 years", "5-10 years", "10+ years"]
    },
    {
        "key": "is_active_trader",
        "question": "Do you actively trade stocks, or are you more of a long-term SIP investor?",
        "options": ["active trader", "SIP investor", "both"]
    },
    {
        "key": "primary_goal",
        "question": "What's the one financial goal you're most focused on right now — saving, growing, protecting, or buying something big?",
        "options": ["saving", "growing", "protecting", "buying"]
    }
]

WARM_OPEN = (
    "Welcome to ET! I'm your personal Financial Navigator. "
    "Before I connect you to the right parts of our ecosystem, "
    "I'd love to understand your financial world. May I ask you "
    "a few quick questions? Takes about 2 minutes."
)


# ─── Persona Determination ────────────────────────────────────────────────────

def determine_persona(answers: Dict[str, Any]) -> PersonaType:
    """Map profiling answers to one of five personas using the LLM natively, falling back to rule-based logic."""
    from config import settings
    import json
    
    # ── Try LLM First ──
    system_prompt = '''You are an expert financial advisor. Analyze the user's profiling answers and assign EXACTLY ONE of the following personas. Respond ONLY with the persona exact name. Do not output anything else.
Personas:
- PERSONA_HOME_BUYER
- PERSONA_ACTIVE_TRADER
- PERSONA_YOUNG_PROFESSIONAL
- PERSONA_CORPORATE_EXECUTIVE
- PERSONA_CONSERVATIVE_SAVER'''

    user_prompt = f"User answers: {json.dumps(answers)}"
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    persona_val = None

    if settings.GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                temperature=0.0,
                max_tokens=32
            )
            content = response.choices[0].message.content.strip().upper().replace(" ", "_").replace("-", "_")
            if content and not content.startswith("PERSONA_"):
                content = f"PERSONA_{content}"
            persona_val = content
        except Exception as e:
            print(f"⚠️ Groq determine_persona failed: {e}")

    if not persona_val:
        ollama_model = getattr(settings, "OLLAMA_MODEL", None)
        if ollama_model:
            try:
                import requests
                res = requests.post(
                    "http://localhost:11434/api/chat",
                    json={"model": ollama_model, "messages": messages, "stream": False},
                    timeout=10,
                ).json()
                content = res.get("message", {}).get("content", "").strip().upper().replace(" ", "_").replace("-", "_")
                if content:
                    if not content.startswith("PERSONA_"):
                        content = f"PERSONA_{content}"
                    persona_val = content
            except Exception as e:
                print(f"⚠️ Ollama determine_persona failed: {e}")

    if persona_val:
        valid_personas = [p.value for p in PersonaType]
        if persona_val in valid_personas:
            return PersonaType(persona_val)

    # ── Fallback Rule-Based Logic ──
    risk = answers.get("risk_score", 5)
    if isinstance(risk, str):
        try:
            risk = int(risk)
        except ValueError:
            risk = 5

    goal = str(answers.get("primary_goal", "")).lower()
    trader = str(answers.get("is_active_trader", "")).lower()
    age = str(answers.get("age_group", "")).lower()
    home = str(answers.get("home_ownership", "")).lower()

    # Home buyer
    if "buying" in goal or (home == "renting" and goal in ("buying", "protecting")):
        return PersonaType.HOME_BUYER

    # Active trader
    if "active" in trader or risk >= 8:
        return PersonaType.ACTIVE_TRADER

    # Young professional
    if age in ("20s", "30s") and risk >= 5:
        return PersonaType.YOUNG_PROFESSIONAL

    # Corporate executive
    if age in ("40s", "50+") and risk >= 5:
        return PersonaType.CORPORATE_EXECUTIVE

    # Default: conservative saver
    return PersonaType.CONSERVATIVE_SAVER


def calculate_profile_completeness(answers: Dict[str, Any]) -> float:
    """Returns profile completeness as a percentage (0.0 – 1.0)."""
    total = len(PROFILING_QUESTIONS)
    answered = sum(1 for q in PROFILING_QUESTIONS if q["key"] in answers and answers[q["key"]])
    return answered / total if total > 0 else 0.0


# ─── Agent Entry Points ──────────────────────────────────────────────────────

def get_onboarding_step(step: int) -> OnboardingResponse:
    """Return the next question for the onboarding flow."""
    if step == 0:
        return OnboardingResponse(
            question=WARM_OPEN,
            step=0,
            is_complete=False,
        )
    
    question_idx = step - 1
    if question_idx < len(PROFILING_QUESTIONS):
        q = PROFILING_QUESTIONS[question_idx]
        return OnboardingResponse(
            question=q["question"],
            step=step,
            is_complete=False,
        )
    
    return OnboardingResponse(step=step, is_complete=True)


def process_onboarding_answer(step: int, answer: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    """Process a user's answer and store it."""
    question_idx = step - 1
    if 0 <= question_idx < len(PROFILING_QUESTIONS):
        key = PROFILING_QUESTIONS[question_idx]["key"]
        # Parse specific types
        if key == "risk_score":
            try:
                answers[key] = int(answer)
            except ValueError:
                answers[key] = 5
        elif key == "has_emergency_fund":
            answers[key] = answer.lower().strip() in ("yes", "y", "true")
        elif key == "is_active_trader":
            answers[key] = answer.lower().strip()
        elif key == "interests":
            answers[key] = [s.strip() for s in answer.split(",")]
        else:
            answers[key] = answer.strip()
    return answers


def complete_profiling(answers: Dict[str, Any]) -> Dict[str, Any]:
    """Finalize the profiling: determine persona and return recommendations."""
    persona = determine_persona(answers)
    mapping = PERSONA_MAPPING[persona]

    tools = [
        {"name": t, "type": "tool", "description": f"Recommended for your {persona.value} profile"}
        for t in mapping["primary_tools"]
    ]

    return {
        "persona": persona.value,
        "recommended_tools": tools,
        "et_prime_sections": mapping["et_prime_sections"],
        "masterclass": mapping["masterclass"],
        "marketplace_products": mapping["marketplace_products"],
        "profile_completeness": calculate_profile_completeness(answers),
        "answers": answers,
    }


def run_profiling_agent(user_message: str, profile: UserProfile) -> AgentResponse:
    """
    Process a message through the profiling agent.
    Used by the orchestrator when routing to profiling.
    """
    # If profile is already complete, return a summary
    if profile.onboarding_complete:
        mapping = PERSONA_MAPPING.get(profile.persona, {})
        tools_str = ", ".join(mapping.get("primary_tools", []))
        return AgentResponse(
            agent_id="profiling_agent",
            content=(
                f"Your profile is already set up! You're mapped as a **{profile.persona.value}**. "
                f"Your recommended tools: {tools_str}. "
                "Would you like to update your preferences?"
            ),
            type="profile_summary",
        )

    # Otherwise, start the onboarding
    return AgentResponse(
        agent_id="profiling_agent",
        content=WARM_OPEN + "\n\n" + PROFILING_QUESTIONS[0]["question"],
        type="onboarding_question",
    )


# ─── Financial X-Ray (LLM-Driven 5-Question Onboarding) ─────────────────────

XRAY_SYSTEM_PROMPT = """You are the ET AI Concierge's Financial X-Ray module — a warm, conversational financial profiler for The Economic Times ecosystem.

Your job is to conduct a 5-question onboarding interview to understand a new user's financial profile. You must ask exactly 5 questions, one at a time, adapting each follow-up based on the user's previous answers.

## Topics to Cover (in this order):
1. **Income type**: Are they salaried, self-employed, or a business owner?
2. **Age group**: Which decade of life are they in (20s, 30s, 40s, 50+)?
3. **Risk tolerance**: How comfortable are they with short-term losses for long-term growth? (scale 1-10)
4. **Investment interests**: Which sectors or asset classes interest them most?
5. **Primary financial goal**: What's their #1 focus — saving, growing wealth, protecting assets, or buying something big?

## Rules:
- Ask ONE question at a time. Never ask more than one.
- Be conversational, warm, and brief. Use natural language, not robotic phrasing.
- Dynamically adapt your question wording based on previous answers. For example, if they say they're in their 20s and salaried, you might frame the risk tolerance question as "Since you're early in your career, you have time on your side. How comfortable are you with short-term dips in your portfolio?"
- Never repeat a question the user has already answered.
- Keep each question under 2 sentences.
- Do NOT give financial advice during the interview.

## When all 5 questions are answered:
After the user answers the 5th question, respond with a brief, encouraging summary message followed by a JSON block in this exact format:

```json
{"xray_complete": true, "profile": {"income_type": "...", "age_group": "...", "risk_score": N, "interests": ["..."], "primary_goal": "...", "persona": "..."}}
```

The JSON block MUST be the last thing in your response. Values should be extracted/normalized from the user's answers:
- income_type: one of "salaried", "self-employed", "business owner"
- age_group: one of "20s", "30s", "40s", "50+"
- risk_score: integer 1-10
- interests: array of sectors like ["Tech", "Pharma", "Banking", "Infrastructure", "Auto", "Real Estate", "FMCG", "Gold", "Crypto"]
- primary_goal: one of "saving", "growing", "protecting", "buying"
- persona: Analyze their answers holistically and use your judgment as an expert financial advisor to assign EXACTLY ONE of the following personas. Do not rely on simplistic rules; look at the entire picture of their risk, age, income, and goals:
   - "PERSONA_HOME_BUYER": Primary focus is saving/planning for a home or real estate.
   - "PERSONA_ACTIVE_TRADER": Very high risk tolerance, actively pursuing aggressive market growth.
   - "PERSONA_YOUNG_PROFESSIONAL": Early in career (20s/30s), building wealth, moderate-to-high risk tolerance.
   - "PERSONA_CORPORATE_EXECUTIVE": Established (40s/50+), business owners/executives managing and protecting significant assets.
   - "PERSONA_CONSERVATIVE_SAVER": Low risk tolerance, prioritizes capital preservation and safe returns above all else.
"""

XRAY_WARM_OPEN = (
    "Welcome to ET! 👋 I'm your personal Financial Navigator. "
    "Before I connect you to the right parts of our ecosystem, "
    "I'd love to understand your financial world through a quick **Financial X-Ray**. "
    "Just 5 quick questions — takes about 2 minutes.\n\n"
)

XRAY_FALLBACK_QUESTIONS = [
    "Let's start simple — are you currently **salaried**, **self-employed**, or a **business owner**?",
    "Which age bracket are you in — **20s**, **30s**, **40s**, or **50+**?",
    "On a scale of **1 to 10**, how comfortable are you with short-term portfolio losses in exchange for long-term growth?",
    "Which sectors interest you the most? For example — **Tech, Pharma, Infrastructure, Banking, Real Estate**?",
    "What's the one financial goal you're most focused on right now — **saving**, **growing wealth**, **protecting assets**, or **buying something big**?",
]


def run_xray_step(
    conversation_history: list,
    question_number: int,
) -> str:
    """
    Use the LLM to generate the next Financial X-Ray question dynamically,
    or fall back to static questions if no LLM is available.

    Args:
        conversation_history: List of {"role": str, "content": str} dicts
        question_number: 0-indexed, which question we're on (0-4)

    Returns:
        The next question or the final summary with JSON profile
    """
    from config import settings

    # Build messages for the LLM
    messages = [{"role": "system", "content": XRAY_SYSTEM_PROMPT}]
    messages.extend(conversation_history)

    # Try Groq first
    if settings.GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=512,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Groq X-Ray failed: {e}")

    # Try local Ollama
    ollama_model = getattr(settings, "OLLAMA_MODEL", None)
    if ollama_model:
        try:
            import requests
            res = requests.post(
                "http://localhost:11434/api/chat",
                json={"model": ollama_model, "messages": messages, "stream": False},
                timeout=20,
            ).json()
            content = res.get("message", {}).get("content", "")
            if content:
                return content
        except Exception as e:
            print(f"⚠️ Ollama X-Ray failed: {e}")

    # Fallback to static questions
    if question_number < len(XRAY_FALLBACK_QUESTIONS):
        return XRAY_FALLBACK_QUESTIONS[question_number]

    # Extract answers from conversation_history
    income = conversation_history[1]["content"] if len(conversation_history) > 1 else "salaried"
    age = conversation_history[3]["content"] if len(conversation_history) > 3 else "30s"
    risk_str = conversation_history[5]["content"] if len(conversation_history) > 5 else "5"
    try:
        risk = int(risk_str)
    except:
        risk = 5
    interests = [conversation_history[7]["content"]] if len(conversation_history) > 7 else ["Tech"]
    goal = conversation_history[9]["content"] if len(conversation_history) > 9 else "growing"
    
    import json
    fallback_profile = {
        "xray_complete": True,
        "profile": {
            "income_type": income.lower(),
            "age_group": age.lower(),
            "risk_score": risk,
            "interests": interests,
            "primary_goal": goal.lower()
        }
    }
    
    # Fallback final response (this shouldn't normally happen)
    return (
        "Thanks for completing the Financial X-Ray! "
        'Based on your answers, I\'ll set up your personalized experience.\n\n'
        f'```json\n{json.dumps(fallback_profile)}\n```'
    )


def extract_xray_profile(llm_response: str) -> Optional[Dict[str, Any]]:
    """
    Extract the JSON profile block from the LLM's final X-Ray response.
    Returns None if no valid profile JSON is found.
    """
    import re
    # Look for JSON block in ```json ... ``` or raw JSON
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', llm_response, re.DOTALL)
    if not json_match:
        json_match = re.search(r'(\{"xray_complete".*?\})', llm_response, re.DOTALL)

    if json_match:
        try:
            data = json.loads(json_match.group(1))
            if data.get("xray_complete") and "profile" in data:
                return data["profile"]
        except json.JSONDecodeError:
            pass
    return None


def map_xray_to_persona(profile_data: Dict[str, Any]) -> str:
    """Map extracted X-Ray profile data to a persona using the LLM's choice, falling back to rule-based logic."""
    # If the LLM assigned a persona, use it directly
    if "persona" in profile_data and profile_data["persona"]:
        persona_val = str(profile_data["persona"]).upper().replace(" ", "_").replace("-", "_")
        if not persona_val.startswith("PERSONA_"):
            persona_val = f"PERSONA_{persona_val}"
            
        valid_personas = [p.value for p in PersonaType]
        if persona_val in valid_personas:
            return persona_val

    # Fallback rule-based logic in case LLM fails to output persona
    risk = profile_data.get("risk_score", 5)
    goal = str(profile_data.get("primary_goal", "")).lower()
    age = str(profile_data.get("age_group", "")).lower()

    if "buying" in goal:
        return PersonaType.HOME_BUYER.value
    if risk >= 8:
        return PersonaType.ACTIVE_TRADER.value
    if age in ("20s", "30s") and risk >= 5:
        return PersonaType.YOUNG_PROFESSIONAL.value
    if age in ("40s", "50+") and risk >= 5:
        return PersonaType.CORPORATE_EXECUTIVE.value
    return PersonaType.CONSERVATIVE_SAVER.value
