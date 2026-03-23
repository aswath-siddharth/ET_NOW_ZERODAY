"""
ET AI Concierge — Intent Router (Agent 1 for Phase 3)
Detects cross-sell and upsell opportunities using a lightweight LLM pre-check.
"""
import json
from typing import Dict, Any
from state import UserProfile
from config import settings

ROUTER_PROMPT = """You are an intent routing assistant for a financial platform.
Your job is to evaluate a user's question and their financial profile to detect cross-sell opportunities.

You MUST respond with a perfectly valid JSON object in exactly this format:
{"trigger_active": true/false, "trigger_type": "string or null"}

Here are the strict triggers you can choose from:

1. "tax_marketplace": Set this ONLY IF the user is asking about tax savings, 80C, ELSS, or deductions, AND their profile indicates they do NOT already have tax investments (has_tax_investments == false).
2. "insurance_marketplace": Set this ONLY IF the user is asking about protecting assets, life insurance, health cover, or term plans, AND their profile indicates they do NOT already have adequate insurance (has_insurance == false).

If the user's question does not strongly match these triggers, or if they already have the respective products according to their profile, set trigger_active to false and trigger_type to null.
Do NOT output any markdown, explanations, or text outside the JSON block. ONLY the raw JSON.
"""

def detect_upsell_intent(query: str, profile: UserProfile) -> Dict[str, Any]:
    """
    Evaluates the user's query and profile to detect monetization intent.
    Returns: {"trigger_active": bool, "trigger_type": str}
    """
    # Default safe fallback
    fallback_response = {"trigger_active": False, "trigger_type": None}

    # If using Groq (Fastest for routing)
    if settings.GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)
            
            user_context = (
                f"User Profile:\n"
                f"- Age Group: {profile.age_group}\n"
                f"- Income Type: {profile.income_type}\n"
                f"- Primary Goal: {profile.primary_goal}\n"
                f"- Persona: {profile.persona.value if profile.persona and hasattr(profile.persona, 'value') else str(profile.persona)}\n"
                f"- Has Tax Investments: {'true' if profile.has_tax_investments else 'false'}\n"
                f"- Has Insurance: {'true' if profile.has_insurance else 'false'}\n\n"
                f"User's Latest Query:\n\"{query}\""
            )

            response = client.chat.completions.create(
                model="llama3-8b-8192", # Using smaller/faster model for quick intent routing
                messages=[
                    {"role": "system", "content": ROUTER_PROMPT},
                    {"role": "user", "content": user_context},
                ],
                temperature=0.0, # Deterministic JSON
                max_tokens=100,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            print(f"⚠️ Intent Router (Groq) failed: {e}")
            return fallback_response

    # If using Ollama
    ollama_model = getattr(settings, "OLLAMA_MODEL", None)
    if ollama_model:
        try:
            import requests
            user_context = (
                f"User Profile:\n"
                f"- Age Group: {profile.age_group}\n"
                f"- Income Type: {profile.income_type}\n"
                f"- Primary Goal: {profile.primary_goal}\n"
                f"- Persona: {profile.persona.value if profile.persona and hasattr(profile.persona, 'value') else profile.persona}\n"
                f"- Has Tax Investments: {'true' if profile.has_tax_investments else 'false'}\n"
                f"- Has Insurance: {'true' if profile.has_insurance else 'false'}\n\n"
                f"User's Latest Query:\n\"{query}\""
            )

            res = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": ollama_model, 
                    "messages": [
                        {"role": "system", "content": ROUTER_PROMPT},
                        {"role": "user", "content": user_context}
                    ], 
                    "stream": False,
                    "format": "json"
                },
                timeout=10,
            ).json()
            content = res.get("message", {}).get("content", "")
            if content:
                return json.loads(content)
        except Exception as e:
            print(f"⚠️ Intent Router (Ollama) failed: {e}")
            
    return fallback_response
