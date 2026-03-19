"""
ET AI Concierge — Behavioral Monitor Agent (Agent 5)
Passive agent that tracks user behavior and fires cross-sell triggers.
"""
from typing import List, Dict, Any, Optional
from state import BehavioralSession, AgentResponse, Recommendation


# ─── Behavioral Triggers ──────────────────────────────────────────────────────

BEHAVIORAL_TRIGGERS = [
    {
        "name": "PAYWALL_HIT_3X",
        "condition": lambda s: s.paywall_hits >= 3,
        "action": "offer_et_prime_discounted",
        "message": "You've hit the ET Prime limit 3 times today. Get 1+1 year for ₹999.",
        "deeplink": "https://buy.indiatimes.com/ET/plans"
    },
    {
        "name": "MASTERCLASS_NO_TOOL",
        "condition": lambda s: s.time_on_page.get("technical-analysis-masterclass", 0) > 120
                               and not s.has_used.get("candlestick-screener", False),
        "action": "bridge_learning_to_tool",
        "message": (
            "You've been exploring the Technical Analysis class. Ready to try it live? "
            "The Candlestick Screener on ET Markets lets you apply exactly this."
        ),
        "deeplink": "https://economictimes.indiatimes.com/markets/stocks/recos"
    },
    {
        "name": "CAREER_TRANSITION",
        "condition": lambda s: "educational loan" in s.recent_queries
                               and "investment" in s.recent_queries,
        "action": "suggest_psychology_of_money",
        "message": (
            "Looks like you're navigating a career transition. The Psychology of Money "
            "masterclass has helped thousands of young professionals build wealth early."
        ),
        "deeplink": "https://economictimes.indiatimes.com/masterclass/psychology-of-money"
    },
    {
        "name": "ANNIVERSARY_UPSELL",
        "condition": lambda s: s.days_since_product_signup in [365, 730],
        "action": "suggest_insurance_review",
        "message": (
            "It's been a year since you joined. A quick insurance review could "
            "save you ₹8,000–₹12,000 annually on premiums."
        ),
        "deeplink": "https://economictimes.indiatimes.com/wealth/insure"
    },
    {
        "name": "TAX_SEARCH_INTENT",
        "condition": lambda s: any(
            q in " ".join(s.recent_queries).lower()
            for q in ["save tax", "80c", "tax deduction", "elss"]
        ),
        "action": "route_to_et_wealth_tax",
        "message": (
            "I found an ET Wealth guide on maximizing your 80C limit "
            "and the NPS calculator to see your exact tax saving."
        ),
        "deeplink": "https://economictimes.indiatimes.com/wealth/tax"
    },
]


# ─── Session Tracking ─────────────────────────────────────────────────────────

_sessions: Dict[str, BehavioralSession] = {}


def get_or_create_session(user_id: str) -> BehavioralSession:
    """Get or create a behavioral tracking session."""
    if user_id not in _sessions:
        _sessions[user_id] = BehavioralSession(user_id=user_id)
    return _sessions[user_id]


def track_paywall_hit(user_id: str):
    """Track a paywall hit event."""
    session = get_or_create_session(user_id)
    session.paywall_hits += 1


def track_page_view(user_id: str, page: str):
    """Track a page view."""
    session = get_or_create_session(user_id)
    session.page_views[page] = session.page_views.get(page, 0) + 1


def track_time_on_page(user_id: str, page: str, seconds: float):
    """Track total time spent on a page."""
    session = get_or_create_session(user_id)
    session.time_on_page[page] = session.time_on_page.get(page, 0) + seconds


def track_query(user_id: str, query: str):
    """Track a user query."""
    session = get_or_create_session(user_id)
    session.recent_queries.append(query.lower())
    if len(session.recent_queries) > 50:
        session.recent_queries = session.recent_queries[-50:]


def track_tool_usage(user_id: str, tool: str):
    """Track tool usage."""
    session = get_or_create_session(user_id)
    session.has_used[tool] = True


# ─── Trigger Evaluation ──────────────────────────────────────────────────────

def evaluate_triggers(user_id: str) -> List[Dict[str, Any]]:
    """Evaluate all behavioral triggers and return fired ones."""
    session = get_or_create_session(user_id)
    fired = []

    for trigger in BEHAVIORAL_TRIGGERS:
        try:
            if trigger["condition"](session):
                fired.append({
                    "name": trigger["name"],
                    "action": trigger["action"],
                    "message": trigger["message"],
                    "deeplink": trigger.get("deeplink", ""),
                })
        except Exception:
            continue  # Skip triggers that fail (missing fields, etc.)

    return fired


# ─── Main Agent Function ─────────────────────────────────────────────────────

def run_behavioral_monitor(user_id: str, user_message: str) -> Optional[AgentResponse]:
    """
    Check behavioral triggers and return a cross-sell response if any fire.
    Returns None if no triggers are active.
    """
    # Track the query
    track_query(user_id, user_message)

    # Evaluate triggers
    fired = evaluate_triggers(user_id)

    if not fired:
        return None

    # Build response from the highest-priority fired trigger
    trigger = fired[0]
    recommendations = [
        Recommendation(
            type="cross_sell",
            title=trigger["name"],
            description=trigger["message"],
            deeplink=trigger.get("deeplink"),
            source_agent="behavioral_monitor",
        )
    ]

    return AgentResponse(
        agent_id="behavioral_monitor",
        content=f"💡 {trigger['message']}",
        type="cross_sell",
        recommendations=recommendations,
        confidence_score=0.9,
    )
