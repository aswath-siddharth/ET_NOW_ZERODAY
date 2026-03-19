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


# ─── Live Data Fetchers ────────────────────────────────────────────────────────

import yfinance as yf
from duckduckgo_search import DDGS

def get_real_time_quote(symbol: str) -> Dict[str, Any]:
    """Get real-time stock quote from Yahoo Finance."""
    try:
        ns_symbol = symbol if symbol.startswith("^") else (symbol + ".NS" if not symbol.endswith(".NS") else symbol)
        ticker = yf.Ticker(ns_symbol)
        data = ticker.history(period="1d")
        if data.empty:
            return {"symbol": symbol, "error": f"Symbol {symbol} not found."}
            
        current_price = data['Close'].iloc[-1]
        prev_close = ticker.info.get('previousClose', current_price)
        change = current_price - prev_close
        percent_change = (change / prev_close) * 100 if prev_close else 0
        
        return {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "change": round(change, 2),
            "percent_change": round(percent_change, 2),
            "high": round(data['High'].iloc[-1], 2),
            "low": round(data['Low'].iloc[-1], 2),
            "open": round(data['Open'].iloc[-1], 2),
            "previous_close": round(prev_close, 2)
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}

def finnhub_get_news(category: str = "general") -> List[Dict]:
    """Get market news using DuckDuckGo News Search."""
    try:
        results = DDGS().news(f"India stock market {category}", max_results=5)
        return [{"headline": n["title"], "url": n["url"]} for n in results]
    except Exception:
        return []

def amfi_get_nav(scheme_code: str = "119551") -> Dict[str, Any]:
    """Get mutual fund NAV via live web search."""
    try:
        results = DDGS().text(f"{scheme_code} mutual fund latest NAV moneycontrol", max_results=2)
        summary = " ".join([r['body'] for r in results])
        return {"scheme": scheme_code, "nav": f"Live Data Search: {summary[:100]}...", "date": "Today"}
    except Exception:
        return {"scheme": scheme_code, "nav": "Error fetching live data", "date": ""}


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
            quote = get_real_time_quote("^NSEI" if sym == "NIFTY50" else "^BSESN" if sym == "SENSEX" else sym)
            direction = "🟢" if quote.get("change", 0) >= 0 else "🔴"
            content_parts.append(
                f"{direction} **{sym}**: ₹{quote['current_price']:,.2f} "
                f"({'+' if quote.get('change', 0) >= 0 else ''}{quote.get('change', 0):.2f}, "
                f"{quote.get('percent_change', 0):.2f}%)"
            )
        is_investment_advice = True

    # ── Gold Queries ──
    elif "gold" in msg_lower:
        quote = get_real_time_quote("GC=F") # Gold futures
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
        nifty = get_real_time_quote("^NSEI")
        sensex = get_real_time_quote("^BSESN")
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
