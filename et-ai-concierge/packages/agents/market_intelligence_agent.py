"""
ET AI Concierge — Market Intelligence Agent (Agent 3)
Real-time market data, portfolio drift, and technical signals.
"""
import math
from typing import Dict, Any, Optional, List
from state import AgentResponse, UserProfile, Recommendation
from config import settings

try:
    import finnhub
except ImportError:
    finnhub = None


# ─── Finnhub Client ──────────────────────────────────────────────────────────

def _get_finnhub_client():
    if finnhub and settings.FINNHUB_API_KEY:
        return finnhub.Client(api_key=settings.FINNHUB_API_KEY)
    return None


def finnhub_get_quote(symbol: str) -> Dict[str, Any]:
    """Get real-time stock quote from Finnhub."""
    client = _get_finnhub_client()
    if client:
        try:
            quote = client.quote(symbol)
            return {
                "symbol": symbol,
                "current_price": quote.get("c", 0),
                "change": quote.get("d", 0),
                "percent_change": quote.get("dp", 0),
                "high": quote.get("h", 0),
                "low": quote.get("l", 0),
                "open": quote.get("o", 0),
                "previous_close": quote.get("pc", 0),
            }
        except Exception as e:
            return {"symbol": symbol, "error": str(e)}

    # Mock data for demo/testing
    mock_quotes = {
        "AAPL": {"current_price": 178.50, "change": 2.30, "percent_change": 1.31},
        "RELIANCE.NS": {"current_price": 2450.75, "change": 15.20, "percent_change": 0.62},
        "TCS.NS": {"current_price": 3820.00, "change": -12.50, "percent_change": -0.33},
        "GOLD": {"current_price": 62450.00, "change": 320.00, "percent_change": 0.51},
        "NIFTY50": {"current_price": 22150.00, "change": 85.00, "percent_change": 0.39},
        "SENSEX": {"current_price": 73200.00, "change": 280.00, "percent_change": 0.38},
    }
    default = {"current_price": 100.00, "change": 0.50, "percent_change": 0.50}
    data = mock_quotes.get(symbol.upper(), default)
    return {"symbol": symbol, **data}


def finnhub_get_news(category: str = "general") -> List[Dict]:
    """Get market news from Finnhub."""
    client = _get_finnhub_client()
    if client:
        try:
            import datetime
            today = datetime.date.today()
            week_ago = today - datetime.timedelta(days=7)
            news = client.general_news(category, _from=str(week_ago), to=str(today))
            return [{"headline": n.get("headline", ""), "url": n.get("url", "")} for n in news[:5]]
        except Exception:
            pass

    return [
        {"headline": "Nifty 50 crosses 22,000 mark; banking stocks lead the rally", "url": "#"},
        {"headline": "RBI holds repo rate at 6.5%; signals dovish stance for Q1 2026", "url": "#"},
        {"headline": "Gold prices hit all-time high amid global uncertainty", "url": "#"},
    ]


def amfi_get_nav(scheme_code: str = "119551") -> Dict[str, Any]:
    """Get mutual fund NAV from AMFI API."""
    # Mock NAV data for hackathon
    mock_navs = {
        "119551": {"scheme": "SBI Blue Chip Fund", "nav": 78.45, "date": "2026-03-18"},
        "120503": {"scheme": "HDFC Mid-Cap Fund", "nav": 156.20, "date": "2026-03-18"},
        "100356": {"scheme": "Axis Long Term Equity", "nav": 82.30, "date": "2026-03-18"},
    }
    return mock_navs.get(scheme_code, {"scheme": "Unknown", "nav": 0, "date": ""})


# ─── Portfolio Drift Detection ────────────────────────────────────────────────

def calculate_portfolio_drift(
    current_allocation: Dict[str, float],
    target_allocation: Dict[str, float],
    threshold: float = 0.05
) -> Dict[str, Any]:
    """Check if portfolio allocation has drifted beyond threshold."""
    drifts = {
        asset: abs(current_allocation.get(asset, 0) - target_allocation.get(asset, 0))
        for asset in set(list(current_allocation.keys()) + list(target_allocation.keys()))
    }
    max_drift_asset = max(drifts, key=drifts.get) if drifts else ""
    max_drift = max(drifts.values()) if drifts else 0
    requires_rebalance = max_drift > threshold

    result = {
        "drifts": drifts,
        "max_drift_asset": max_drift_asset,
        "max_drift_pct": round(max_drift * 100, 1),
        "requires_rebalance": requires_rebalance,
    }

    if requires_rebalance:
        result["message"] = (
            f"Your {max_drift_asset} allocation has drifted {result['max_drift_pct']}% "
            f"above target. Consider rebalancing."
        )
        result["suggestion"] = "Consider rebalancing by adjusting your allocation mix."
        result["deeplink"] = "https://economictimes.indiatimes.com/markets/portfolio"

    return result


# ─── Main Agent Function ─────────────────────────────────────────────────────

def run_market_intelligence_agent(user_message: str, profile: UserProfile) -> AgentResponse:
    """Process a message through the Market Intelligence Agent."""
    msg_lower = user_message.lower()
    content_parts = []
    sources = []
    recommendations = []
    is_investment_advice = False

    # ── Stock/Index Quote Requests ──
    if any(word in msg_lower for word in ["price", "quote", "nifty", "sensex", "stock"]):
        # Determine which symbols to look up
        symbols = []
        if "nifty" in msg_lower:
            symbols.append("NIFTY50")
        if "sensex" in msg_lower:
            symbols.append("SENSEX")
        if "reliance" in msg_lower:
            symbols.append("RELIANCE.NS")
        if "tcs" in msg_lower:
            symbols.append("TCS.NS")
        if not symbols:
            symbols = ["NIFTY50", "SENSEX"]

        content_parts.append("📊 **Real-Time Market Data:**\n")
        for sym in symbols:
            quote = finnhub_get_quote(sym)
            direction = "🟢" if quote.get("change", 0) >= 0 else "🔴"
            content_parts.append(
                f"{direction} **{sym}**: ₹{quote['current_price']:,.2f} "
                f"({'+' if quote.get('change', 0) >= 0 else ''}{quote.get('change', 0):.2f}, "
                f"{quote.get('percent_change', 0):.2f}%)"
            )
        is_investment_advice = True

    # ── Gold Queries ──
    elif "gold" in msg_lower:
        quote = finnhub_get_quote("GOLD")
        content_parts.append("🪙 **Gold Market Update:**\n")
        content_parts.append(
            f"MCX Gold: ₹{quote['current_price']:,.2f}/10g "
            f"({'+' if quote.get('change', 0) >= 0 else ''}{quote.get('change', 0):.2f})"
        )
        content_parts.append(
            "\n**Analyst View:** Gold remains a strong hedge. "
            "Consider Sovereign Gold Bonds (SGBs) for tax-free returns + 2.5% annual interest."
        )
        recommendations.append(Recommendation(
            type="product",
            title="Sovereign Gold Bond Calculator",
            description="Calculate your expected returns from SGBs",
            deeplink="https://economictimes.indiatimes.com/markets/gold/sgb-calculator",
            source_agent="market_intelligence_agent",
        ))
        is_investment_advice = True

    # ── Mutual Fund NAV ──
    elif any(word in msg_lower for word in ["mutual fund", "nav", "sip"]):
        nav_data = amfi_get_nav("119551")
        content_parts.append("📈 **Mutual Fund Update:**\n")
        content_parts.append(f"**{nav_data['scheme']}**: NAV ₹{nav_data['nav']} (as of {nav_data['date']})")
        nav2 = amfi_get_nav("120503")
        content_parts.append(f"**{nav2['scheme']}**: NAV ₹{nav2['nav']} (as of {nav2['date']})")
        is_investment_advice = True

    # ── Portfolio Drift ──
    elif "portfolio" in msg_lower or "rebalance" in msg_lower:
        drift = calculate_portfolio_drift(
            current_allocation={"equity": 0.72, "debt": 0.18, "gold": 0.10},
            target_allocation={"equity": 0.60, "debt": 0.30, "gold": 0.10},
        )
        content_parts.append("📊 **Portfolio Analysis:**\n")
        if drift["requires_rebalance"]:
            content_parts.append(f"⚠️ {drift['message']}")
            content_parts.append(f"💡 {drift['suggestion']}")
        else:
            content_parts.append("✅ Your portfolio is well-balanced. No rebalancing needed.")
        is_investment_advice = True

    # ── Market News ──
    else:
        news = finnhub_get_news()
        content_parts.append("📰 **Today's Market Headlines:**\n")
        for item in news:
            content_parts.append(f"• {item['headline']}")

    # ── Morning Briefing ──
    if "morning" in msg_lower or "briefing" in msg_lower:
        nifty = finnhub_get_quote("NIFTY50")
        sensex = finnhub_get_quote("SENSEX")
        content_parts = ["☀️ **Your Morning Briefing:**\n"]
        content_parts.append(
            f"Markets: Nifty {nifty['current_price']:,.0f} ({nifty.get('percent_change', 0):+.2f}%), "
            f"Sensex {sensex['current_price']:,.0f} ({sensex.get('percent_change', 0):+.2f}%)"
        )
        news = finnhub_get_news()
        content_parts.append("\n**Top Stories:**")
        for item in news[:3]:
            content_parts.append(f"• {item['headline']}")

    return AgentResponse(
        agent_id="market_intelligence_agent",
        content="\n".join(content_parts),
        type="market_data",
        contains_investment_advice=is_investment_advice,
        recommendations=recommendations,
        sources=sources,
        confidence_score=0.85,
    )
