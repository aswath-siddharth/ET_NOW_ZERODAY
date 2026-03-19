"""
ET AI Concierge — Editorial Agent (Agent 2)
Surfaces ET Prime / ET Wealth content using the local RAG pipeline.
"""
from typing import List, Dict, Any, Optional
from state import AgentResponse, UserProfile, Recommendation, PersonaType
from config import settings


# ─── Mock ET Prime Article Database ───────────────────────────────────────────
# In production, this is replaced by the full RAG pipeline (Qdrant + Elastic + Neo4j)

MOCK_ARTICLES = [
    {
        "id": "art_001",
        "title": "Gold GIFT City Volumes Plunge 40% — What It Means for Investors",
        "sector": "Markets",
        "summary": "GIFT City's gold trading volumes have dropped significantly. Analysts suggest this could signal a shift in institutional gold appetite.",
        "url": "https://economictimes.indiatimes.com/markets/gold/gift-city-volumes",
        "tags": ["gold", "GIFT City", "institutional", "trading"],
        "paywall": True
    },
    {
        "id": "art_002",
        "title": "Sovereign Gold Bonds vs Physical Gold: 2025 Returns Compared",
        "sector": "Personal Finance",
        "summary": "SGBs delivered 12.8% annualized returns vs 8.2% for physical gold. Tax treatment gives SGBs an additional edge.",
        "url": "https://economictimes.indiatimes.com/wealth/invest/sgb-vs-physical-gold",
        "tags": ["gold", "SGB", "sovereign gold bond", "returns"],
        "paywall": False
    },
    {
        "id": "art_003",
        "title": "Nifty 50 Technical Analysis: Golden Cross Signals Bull Run",
        "sector": "Markets",
        "summary": "Nifty 50 has formed a Golden Cross pattern. Historical data shows 78% probability of 15%+ rally within 6 months.",
        "url": "https://economictimes.indiatimes.com/markets/nifty-golden-cross",
        "tags": ["nifty", "technical analysis", "golden cross", "bull"],
        "paywall": True
    },
    {
        "id": "art_004",
        "title": "RBI Rate Cut: Home Loan EMIs to Drop by ₹1,200/month",
        "sector": "Real Estate",
        "summary": "RBI's 25bps rate cut will reduce home loan EMIs. SBI and HDFC have already passed on the benefit.",
        "url": "https://economictimes.indiatimes.com/wealth/real-estate/rbi-rate-cut-emi",
        "tags": ["RBI", "rate cut", "home loan", "EMI", "SBI", "HDFC"],
        "paywall": False
    },
    {
        "id": "art_005",
        "title": "Best ELSS Funds 2025: Maximize Your Section 80C Savings",
        "sector": "Personal Finance",
        "summary": "Top 5 ELSS funds that combine tax savings with wealth creation. Includes 3-year and 5-year return analysis.",
        "url": "https://economictimes.indiatimes.com/wealth/tax/elss-funds-2025",
        "tags": ["ELSS", "80C", "tax saving", "mutual funds"],
        "paywall": False
    },
    {
        "id": "art_006",
        "title": "Young Mind Entrepreneurs: 5 Startup Founders Under 25",
        "sector": "Startups",
        "summary": "Profiles of India's youngest startup founders, their funding journeys, and lessons for aspiring entrepreneurs.",
        "url": "https://economictimes.indiatimes.com/startups/young-mind-founders",
        "tags": ["startups", "young mind", "entrepreneurs", "founders"],
        "paywall": True
    },
    {
        "id": "art_007",
        "title": "Portfolio Rebalancing Strategy: When to Shift from Equity to Debt",
        "sector": "Markets",
        "summary": "Expert guide on portfolio rebalancing. Includes age-based allocation models and tax-efficient switching strategies.",
        "url": "https://economictimes.indiatimes.com/markets/portfolio-rebalancing",
        "tags": ["portfolio", "rebalancing", "equity", "debt", "allocation"],
        "paywall": True
    },
    {
        "id": "art_008",
        "title": "NPS vs PPF: Which Retirement Plan Wins in 2025?",
        "sector": "Personal Finance",
        "summary": "NPS offers higher returns but with market risk. PPF guarantees 7.1%. We break down which suits your risk profile.",
        "url": "https://economictimes.indiatimes.com/wealth/plan/nps-vs-ppf",
        "tags": ["NPS", "PPF", "retirement", "pension", "saving"],
        "paywall": False
    },
    {
        "id": "art_009",
        "title": "Auto Sector Rally: Tata Motors, M&M Lead the Charge",
        "sector": "Auto",
        "summary": "Auto stocks have surged 25% YTD driven by EV demand and export growth. Should you buy, hold, or sell?",
        "url": "https://economictimes.indiatimes.com/markets/auto-rally",
        "tags": ["auto", "Tata Motors", "M&M", "EV", "stocks"],
        "paywall": True
    },
    {
        "id": "art_010",
        "title": "Health Insurance: Why You Need ₹10 Lakh Cover Minimum in 2025",
        "sector": "Personal Finance",
        "summary": "Medical inflation at 14% means your ₹5 lakh cover is woefully inadequate. Niva Bupa and Star Health compared.",
        "url": "https://economictimes.indiatimes.com/wealth/insure/health-insurance-2025",
        "tags": ["insurance", "health", "Niva Bupa", "Star Health", "cover"],
        "paywall": False
    },
]


def _search_articles(query: str, user_interests: List[str] = None) -> List[Dict]:
    """Simple keyword-based search over mock articles. Replaced by RAG pipeline in production."""
    query_lower = query.lower()
    results = []

    for article in MOCK_ARTICLES:
        score = 0
        # Check title match
        if any(word in article["title"].lower() for word in query_lower.split()):
            score += 3
        # Check tag match
        if any(tag in query_lower for tag in article["tags"]):
            score += 5
        # Check summary match
        if any(word in article["summary"].lower() for word in query_lower.split()):
            score += 1
        # Boost if matches user interests
        if user_interests:
            if article["sector"] in user_interests:
                score += 2

        if score > 0:
            results.append({**article, "_score": score})

    results.sort(key=lambda x: x["_score"], reverse=True)
    return results[:3]


def _apply_paywall_check(articles: List[Dict], has_subscription: bool) -> List[Dict]:
    """Add paywall nudge if user doesn't have ET Prime."""
    processed = []
    for article in articles:
        entry = {**article}
        if article.get("paywall") and not has_subscription:
            entry["paywall_nudge"] = {
                "type": "paywall_nudge",
                "message": "This exclusive analysis is from ET Prime.",
                "cta": "You've read premium stories today. Get full access for ₹199/month.",
                "deeplink": "https://buy.indiatimes.com/ET/plans",
            }
        processed.append(entry)
    return processed


# ─── Context-Sensitive Routing ────────────────────────────────────────────────

def _route_by_persona(query: str, persona: Optional[PersonaType]) -> str:
    """Different personas get different slants on the same query."""
    query_lower = query.lower()

    if "gold" in query_lower:
        if persona == PersonaType.ACTIVE_TRADER:
            return "gold MCX technical analysis trading"
        elif persona == PersonaType.CORPORATE_EXECUTIVE:
            return "gold GIFT City volumes institutional"
        elif persona == PersonaType.CONSERVATIVE_SAVER:
            return "sovereign gold bond vs physical gold returns"
        else:
            return "gold investment options SGB"

    return query  # Unchanged for other queries


# ─── Main Agent Function ─────────────────────────────────────────────────────

def run_editorial_agent(user_message: str, profile: UserProfile) -> AgentResponse:
    """
    Process a message through the Editorial Agent.
    Searches ET Prime corpus and returns personalized content.
    """
    # Route query based on persona
    search_query = _route_by_persona(user_message, profile.persona)

    # Search articles
    articles = _search_articles(search_query, profile.interests)

    # Apply paywall check
    articles = _apply_paywall_check(articles, profile.has_et_prime_subscription)

    if not articles:
        return AgentResponse(
            agent_id="editorial_agent",
            content="I couldn't find specific ET Prime articles matching your query. Let me search our broader knowledge base.",
            type="editorial_search",
            sources=[],
        )

    # Build response
    content_parts = [f"📰 **Here's what I found from ET Prime for you:**\n"]

    recommendations = []
    sources = []
    has_paywall = False

    for i, article in enumerate(articles, 1):
        content_parts.append(f"**{i}. [{article['title']}]({article['url']})**")
        content_parts.append(f"   {article['summary']}\n")
        sources.append(article["url"])

        recommendations.append(Recommendation(
            type="article",
            title=article["title"],
            description=article["summary"],
            deeplink=article["url"],
            source_agent="editorial_agent",
        ))

        if "paywall_nudge" in article:
            has_paywall = True

    if has_paywall:
        content_parts.append(
            "\n💎 *Some of these stories are ET Prime exclusives. "
            "Get full access for ₹199/month at [ET Prime](https://buy.indiatimes.com/ET/plans).*"
        )

    return AgentResponse(
        agent_id="editorial_agent",
        content="\n".join(content_parts),
        type="editorial_search",
        contains_investment_advice="invest" in user_message.lower() or "buy" in user_message.lower(),
        recommendations=recommendations,
        sources=sources,
    )
