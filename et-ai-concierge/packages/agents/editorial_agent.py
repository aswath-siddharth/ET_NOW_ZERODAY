"""
ET AI Concierge — Editorial Agent (Agent 2)
Surfaces ET Prime / ET Wealth content using the RAG pipeline.
Falls back to mock articles if RAG is not available.
"""
from typing import List, Dict, Any, Optional
from state import AgentResponse, UserProfile, Recommendation, PersonaType
from config import settings


# ─── RAG Integration ──────────────────────────────────────────────────────────

def _rag_available() -> bool:
    """Check if the RAG engine is operational."""
    try:
        from rag_engine import retrieve
        # Quick check — does the knowledge_base table have data?
        results = retrieve("test", top_k=1)
        return len(results) > 0
    except Exception:
        return False


def _search_with_rag(query: str, persona: Optional[str] = None) -> Dict[str, Any]:
    """Use the RAG engine for retrieval + generation."""
    try:
        from rag_engine import ask
        result = ask(query, persona=persona, top_k=3)
        return result
    except Exception as e:
        print(f"⚠️ RAG search failed: {e}")
        return None


# ─── Fallback: Mock ET Prime Article Database ────────────────────────────────
# Used when RAG is not available (no pgvector, no embeddings, etc.)

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
]


def _search_articles(query: str, user_interests: List[str] = None) -> List[Dict]:
    """Simple keyword-based search over mock articles (fallback)."""
    query_lower = query.lower()
    results = []

    for article in MOCK_ARTICLES:
        score = 0
        if any(word in article["title"].lower() for word in query_lower.split()):
            score += 3
        if any(tag in query_lower for tag in article["tags"]):
            score += 5
        if any(word in article["summary"].lower() for word in query_lower.split()):
            score += 1
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

    return query


# ─── Main Agent Function ─────────────────────────────────────────────────────

def run_editorial_agent(user_message: str, profile: UserProfile) -> AgentResponse:
    """
    Process a message through the Editorial Agent.
    Uses RAG pipeline if available, falls back to mock articles.
    """
    if profile.persona:
        persona_str = profile.persona.value if hasattr(profile.persona, 'value') else str(profile.persona)
    else:
        persona_str = None

    # ═══ Try RAG Pipeline First ═══
    rag_result = _search_with_rag(user_message, persona=persona_str)

    if rag_result and rag_result.get("chunks_used", 0) > 0:
        # RAG succeeded — build response from RAG output
        content = rag_result["answer"]

        # Add source links
        sources = rag_result.get("sources", [])
        source_urls = [s["url"] for s in sources if s.get("url")]

        has_paywall = any(s.get("paywall", False) for s in sources)
        if has_paywall and not profile.has_et_prime_subscription:
            content += (
                "\n\n💎 *Some of this content is from ET Prime exclusives. "
                "Get full access for ₹199/month at [ET Prime](https://buy.indiatimes.com/ET/plans).*"
            )

        recommendations = [
            Recommendation(
                type="article",
                title=s["title"],
                description="",
                deeplink=s.get("url", ""),
                source_agent="editorial_agent",
            )
            for s in sources
        ]

        return AgentResponse(
            agent_id="editorial_agent",
            content=content,
            type="rag_response",
            contains_investment_advice="invest" in user_message.lower() or "buy" in user_message.lower(),
            recommendations=recommendations,
            sources=source_urls,
        )

    # ═══ Fallback: Mock Articles ═══
    search_query = _route_by_persona(user_message, profile.persona)
    articles = _search_articles(search_query, profile.interests)
    articles = _apply_paywall_check(articles, profile.has_et_prime_subscription)

    if not articles:
        return AgentResponse(
            agent_id="editorial_agent",
            content="I couldn't find specific ET Prime articles matching your query. Let me search our broader knowledge base.",
            type="editorial_search",
            sources=[],
        )

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
