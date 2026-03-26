"""
ET AI Concierge — Intent Router (Agent 1 for Phase 3)
Detects cross-sell and upsell opportunities using a lightweight LLM pre-check.
"""
import json
from typing import Dict, Any
from state import UserProfile
from config import settings

ROUTER_PROMPT = """You are an intent routing assistant for a financial platform.
Your job is to detect if a user is asking about financial products to trigger marketplace recommendations.

IMPORTANT: Respond with ONLY a JSON object on a single line:
{"trigger_active": true/false, "trigger_type": "tax_marketplace" or "insurance_marketplace" or null}

Trigger conditions:

1. "tax_marketplace" trigger:
   - User is asking about: saving taxes, 80C, section 80C, ELSS, mutual funds for taxes, deductions, tax-saving investments, FD tax benefits, NPS tax benefits
   - AND profile shows: has_tax_investments is false (meaning they DON'T have tax products yet)
   - If has_tax_investments is true, DO NOT trigger

2. "insurance_marketplace" trigger:
   - User is asking about: life insurance, health insurance, term plan, health cover, insurance products, asset protection, family protection
   - AND profile shows: has_insurance is false (meaning they DON'T have insurance yet)
   - If has_insurance is true, DO NOT trigger

Logic:
- Check the query carefully for tax or insurance keywords
- Check the corresponding profile flag
- If keyword match AND profile flag is false → trigger it (trigger_active=true)
- Otherwise → no trigger (trigger_active=false, trigger_type=null)
- Output ONLY JSON, nothing else
- Example: {"trigger_active": true, "trigger_type": "tax_marketplace"}
"""

def detect_upsell_intent(query: str, profile: UserProfile) -> Dict[str, Any]:
    """
    Evaluates the user's query and profile to detect monetization intent.
    Uses OpenRouter primarily, falls back to keyword matching if needed.
    Returns: {"trigger_active": bool, "trigger_type": str or None}
    
    Critical for upselling. Retries on failure to ensure reliability.
    """
    # Default safe fallback
    fallback_response = {"trigger_active": False, "trigger_type": None}

    # Debug: Show profile flags
    print(f"[DEBUG] Profile flags - tax_investments={profile.has_tax_investments}, insurance={profile.has_insurance}")

    # ──── SIMPLE KEYWORD FALLBACK (Most Reliable) ────────────────────────────
    query_lower = query.lower()
    
    # Tax keywords
    tax_keywords = ["80c", "section 80c", "elss", "tax sav", "tax invest", "tax deduct", "tax-sav", "tax-invest", "tax benefit", "fy deduct"]
    if any(kw in query_lower for kw in tax_keywords) and not profile.has_tax_investments:
        print(f"[OK] Keyword match: tax_marketplace detected")
        return {"trigger_active": True, "trigger_type": "tax_marketplace"}
    
    # Insurance keywords
    insurance_keywords = ["life insur", "health insur", "term plan", "insur cover", "insur plan", "protect", "health cover"]
    if any(kw in query_lower for kw in insurance_keywords) and not profile.has_insurance:
        print(f"[OK] Keyword match: insurance_marketplace detected")
        return {"trigger_active": True, "trigger_type": "insurance_marketplace"}

    # ──── TRY OPENROUTER AS BACKUP ────────────────────────────────────────────
    user_context = (
        f"User Profile:\\n"
        f"- Age Group: {profile.age_group}\\n"
        f"- Income Type: {profile.income_type}\\n"
        f"- Primary Goal: {profile.primary_goal}\\n"
        f"- Persona: {profile.persona.value if profile.persona and hasattr(profile.persona, 'value') else str(profile.persona)}\\n"
        f"- Has Tax Investments: {'true' if profile.has_tax_investments else 'false'}\\n"
        f"- Has Insurance: {'true' if profile.has_insurance else 'false'}\\n\\n"
        f"User's Latest Query:\\n\\\"{query}\\\""
    )

    # Retry up to 1 time for OpenRouter (keyword matching is primary)
    max_retries = 1
    for attempt in range(max_retries):
        if not settings.OPENROUTER_API_KEY:
            return fallback_response
            
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://et-ai-concierge.local",
                "X-Title": "ET AI Concierge",
            }
            payload = {
                "model": settings.OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": ROUTER_PROMPT},
                    {"role": "user", "content": user_context},
                ],
                "temperature": 0.0,
                "max_tokens": 50,
            }
            
            response = requests.post(settings.OPENROUTER_URL, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            resp_data = response.json()
            
            if "choices" in resp_data and resp_data["choices"]:
                content = resp_data["choices"][0]["message"].get("content", "").strip()
                
                if content:
                    try:
                        result = json.loads(content)
                        if isinstance(result, dict) and "trigger_active" in result and "trigger_type" in result:
                            print(f"[DEBUG] OpenRouter response: trigger_active={result.get('trigger_active')}, trigger_type={result.get('trigger_type')}")
                            if result.get("trigger_active"):
                                print(f"[OK] OpenRouter detected: {result.get('trigger_type')}")
                            return result
                    except json.JSONDecodeError:
                        if '{' in content:
                            json_start = content.find('{')
                            json_end = content.rfind('}') + 1
                            if json_start >= 0 and json_end > json_start:
                                try:
                                    result = json.loads(content[json_start:json_end])
                                    if isinstance(result, dict) and "trigger_active" in result and "trigger_type" in result:
                                        print(f"[DEBUG] OpenRouter response (extracted): trigger_active={result.get('trigger_active')}, trigger_type={result.get('trigger_type')}")
                                        if result.get("trigger_active"):
                                            print(f"[OK] OpenRouter detected: {result.get('trigger_type')}")
                                        return result
                                except json.JSONDecodeError:
                                    pass
                
        except Exception as e:
            pass
    
    # All methods failed, return safe default
    return fallback_response
