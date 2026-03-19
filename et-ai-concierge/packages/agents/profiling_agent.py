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
    """Map profiling answers to one of five personas using rule-based logic."""
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
    if goal == "buying" or (home == "renting" and goal in ("buying", "protecting")):
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
