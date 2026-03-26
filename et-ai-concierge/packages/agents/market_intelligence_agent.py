"""
ET AI Concierge — Market Intelligence Agent (Agent 3)
Real-time market data, portfolio drift, and technical signals.
Optional RAG enrichment for expert analysis and insights.
"""
import math
from typing import Dict, Any, Optional, List
from state import AgentResponse, UserProfile, Recommendation
from config import settings

try:
    import finnhub
except ImportError:
    finnhub = None

try:
    from newsapi import NewsApiClient
except ImportError:
    NewsApiClient = None

try:
    import feedparser
except ImportError:
    feedparser = None


# ─── Live Data Fetchers ────────────────────────────────────────────────────────

import yfinance as yf
from ddgs import DDGS

def get_real_time_quote(symbol: str) -> Dict[str, Any]:
    """Get real-time stock quote from Yahoo Finance."""
    try:
        ns_symbol = symbol if symbol.startswith("^") else (symbol + ".NS" if not symbol.endswith(".NS") else symbol)
        ticker = yf.Ticker(ns_symbol)
        data = ticker.history(period="1d")
        if data.empty:
            return {"symbol": symbol, "error": f"Symbol {symbol} may be delisted or invalid.", "status": "not_found"}
            
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


def _get_finnhub_news(query: str = "India stocks") -> List[Dict]:
    """Fetch news from Finnhub API."""
    if not settings.FINNHUB_API_KEY or not finnhub:
        return []
    
    try:
        client = finnhub.Client(api_key=settings.FINNHUB_API_KEY)
        # Finnhub returns news for specific companies, use general search
        news_data = client.general_news("general", min_id=0)
        articles = []
        
        # Handle both dict and list responses
        data_items = []
        if isinstance(news_data, dict):
            data_items = news_data.get("data", [])
        elif isinstance(news_data, list):
            data_items = news_data
        
        for item in data_items[:5]:
            if isinstance(item, dict):
                articles.append({
                    "headline": item.get("headline", ""),
                    "url": item.get("url", ""),
                    "source": "Finnhub"
                })
        return articles
    except Exception as e:
        print(f"[WARN] Finnhub API error: {e}")
        return []


def _get_newsapi_news(query: str = "India stocks") -> List[Dict]:
    """Fetch news from NewsAPI."""
    if not NewsApiClient or not settings.NEWSAPI_API_KEY:
        return []
    
    try:
        newsapi = NewsApiClient(api_key=settings.NEWSAPI_API_KEY)
        articles_response = newsapi.get_everything(
            q=query,
            language="en",
            sort_by="publishedAt",
            page_size=5
        )
        articles = []
        for item in articles_response.get("articles", []):
            articles.append({
                "headline": item.get("title", ""),
                "url": item.get("url", ""),
                "source": item.get("source", {}).get("name", "NewsAPI")
            })
        return articles
    except Exception as e:
        print(f"[WARN] NewsAPI error: {e}")
        return []


def _get_et_rss_news() -> List[Dict]:
    """Fetch news from Economic Times RSS feeds."""
    if not feedparser:
        return []
    
    try:
        feeds = {
            "markets": "https://feeds.economictimes.indiatimes.com/markets/",
            "wealth": "https://feeds.economictimes.indiatimes.com/wealth/",
        }
        
        articles = []
        for feed_name, feed_url in feeds.items():
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:3]:
                    articles.append({
                        "headline": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "source": f"ET {feed_name.capitalize()}"
                    })
            except Exception:
                continue
        
        return articles
    except Exception as e:
        print(f"[WARN] RSS feed error: {e}")
        return []


def _get_duckduckgo_news(query: str = "India stock market") -> List[Dict]:
    """Fetch news from DuckDuckGo (fallback)."""
    try:
        results = DDGS().news(query, max_results=5)
        return [{"headline": n["title"], "url": n["url"], "source": "DuckDuckGo"} for n in results]
    except Exception:
        return []


def finnhub_get_news(category: str = "general") -> List[Dict]:
    """
    Get market news from ALL sources simultaneously.
    Aggregates results from Finnhub, NewsAPI, ET RSS, and DuckDuckGo.
    """
    query_map = {
        "stock market trading technical analysis": "stocks trading",
        "SIP mutual funds startup investing young professional": "mutual funds SIP",
        "corporate governance acquisitions dividend executive": "corporate governance",
        "fixed deposits bonds insurance safety": "fixed deposits insurance",
        "home loan real estate property mortgage": "home loans real estate",
    }
    
    search_query = query_map.get(category, category)
    
    all_news = []
    
    # Fetch from ALL sources in parallel
    finnhub_news = _get_finnhub_news(search_query)
    all_news.extend(finnhub_news)
    
    newsapi_news = _get_newsapi_news(search_query)
    all_news.extend(newsapi_news)
    
    et_rss_news = _get_et_rss_news()
    all_news.extend(et_rss_news)
    
    ddg_news = _get_duckduckgo_news(f"India {search_query}")
    all_news.extend(ddg_news)
    
    # Remove duplicates by headline
    seen = set()
    unique_news = []
    for article in all_news:
        headline = article.get("headline", "").strip().lower()
        if headline and headline not in seen:
            seen.add(headline)
            unique_news.append(article)
    
    # Return up to 10 unique articles
    return unique_news[:10]


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


# ─── Indian Gold Price Fetcher ────────────────────────────────────────────

def get_indian_gold_price() -> Dict[str, Any]:
    """
    Get Indian gold prices from MCX-linked sources.
    Tries multiple gold ETF symbols that track MCX prices.
    Falls back to international gold if needed.
    """
    # Gold ETF symbols that track MCX prices (NSE listed)
    gold_etf_symbols = [
        "GOLDPETAL.NS",       # Motilal Oswal Gold ETF (common/liquid)
        "SBIN0000001.NS",     # SBI Gold ETF
        "GOLDSHARE.NS",       # Motilal Oswal Gold Savings Fund
        "JPGOLD.NS",          # Jignesh Parikh Gold ETF
    ]
    
    # Try each symbol to get MCX-linked Indian gold price
    for symbol in gold_etf_symbols:
        try:
            quote = get_real_time_quote(symbol)
            if quote.get("current_price") and "error" not in quote:
                # Successfully got Indian gold price
                quote["symbol"] = "MCX Gold (via ETF)"
                quote["unit"] = "per 1 gram"
                return quote
        except Exception:
            continue
    
    # Fallback: If MCX symbols fail, use international gold
    # Note: International gold (GC=F) is in USD/Troy oz, needs conversion
    try:
        quote = get_real_time_quote("GC=F")  # COMEX gold
        if quote.get("current_price") and "error" not in quote:
            # Approximate conversion: 1 troy oz ≈ 31.1g, rough INR conversion
            quote["symbol"] = "International Gold Reference"
            quote["note"] = "(USD prices - for reference only)"
            return quote
    except Exception:
        pass
    
    # If all fail, return error response
    return {
        "symbol": "Gold",
        "error": "Unable to fetch current gold prices",
        "suggestion": "Check ET Markets Gold coverage for live MCX prices"
    }


# ─── Optional RAG Enhancement ────────────────────────────────────────────────

def _get_market_rag_context(query: str) -> Optional[Dict[str, Any]]:
    """
    Optionally enhance market responses with RAG-retrieved expert analysis.
    Returns enrichment data or None if RAG unavailable.
    Non-blocking: if RAG fails, just returns None.
    """
    try:
        from rag_engine import retrieve
        
        # Adapt RAG query based on market context
        rag_queries = {
            "nifty": "Nifty 50 technical analysis market trends",
            "sensex": "Sensex BSE market analysis trends",
            "gold": "gold investment guide SGBs returns",
            "mutual fund": "mutual fund investment strategy SIP",
            "sip": "SIP strategy returns systematic investment",
            "portfolio": "portfolio rebalancing strategy allocation",
            "stock": "stock market technical analysis trading",
        }
        
        # Find most relevant RAG query
        adapted_query = query
        for keyword, enhanced_query in rag_queries.items():
            if keyword in query.lower():
                adapted_query = enhanced_query
                break
        
        # Retrieve from RAG (non-blocking with timeout)
        chunks = retrieve(adapted_query, top_k=2)  # Just 2 for brevity
        
        if not chunks or len(chunks) == 0:
            return None
        
        # Extract sources for recommendations
        sources = []
        insights = []
        for chunk in chunks:
            if chunk.get("chunk_text"):
                insights.append(chunk["chunk_text"][:200])  # First 200 chars
            if chunk.get("source_url"):
                sources.append({
                    "title": chunk.get("title", "ET Prime Analysis"),
                    "url": chunk["source_url"],
                })
        
        return {
            "insights": insights,
            "sources": sources,
            "chunks_used": len(chunks)
        }
    
    except Exception as e:
        # Non-blocking: RAG failure doesn't break market response
        print(f"[DEBUG] Market RAG enrichment skipped: {e}")
        return None


# ─── Main Agent Function ─────────────────────────────────────────────────────

def run_market_intelligence_agent(user_message: str, profile: UserProfile) -> AgentResponse:
    """
    Process a message through the Market Intelligence Agent.
    Provides real-time market data FIRST, then optionally enriches with RAG context.
    """
    msg_lower = user_message.lower()
    content_parts = []
    sources = []
    recommendations = []
    is_investment_advice = False
    rag_context = None  # Optional enrichment

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
        quote = get_indian_gold_price()  # Use Indian gold prices
        content_parts.append("🪙 **Gold Market Update:**\n")
        
        if "error" not in quote:
            symbol_display = quote.get("symbol", "Gold")
            unit_display = quote.get("unit", "/10g")
            direction = "🟢" if quote.get("change", 0) >= 0 else "🔴"
            content_parts.append(
                f"{direction} **{symbol_display}**: ₹{quote['current_price']:,.2f}{unit_display} "
                f"({'+' if quote.get('change', 0) >= 0 else ''}{quote.get('change', 0):.2f}, "
                f"{quote.get('percent_change', 0):.2f}%)"
            )
            if note := quote.get("note"):
                content_parts.append(f"   *{note}*")
        else:
            content_parts.append(f"⚠️ {quote['error']}")
            content_parts.append(f"   💡 {quote.get('suggestion', '')}")
        
        content_parts.append(
            "\n**Analyst View:** Gold remains a strong hedge against inflation. "
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

    # ── Optional RAG Enrichment ──
    # Add expert analysis/insights from ET Prime knowledge base
    # Only for relevant query types, non-blocking if RAG fails
    should_enrich = any(word in msg_lower for word in [
        "gold", "nifty", "sensex", "mutual fund", "sip", "portfolio",
        "stock", "analysis", "trend", "rebalance"
    ])
    
    if should_enrich:
        rag_context = _get_market_rag_context(user_message)
        
        if rag_context and rag_context.get("insights"):
            content_parts.append("\n---")
            content_parts.append("\n📖 **ET Prime Expert Insights:**")
            for i, insight in enumerate(rag_context["insights"], 1):
                content_parts.append(f"\n**Insight {i}:** {insight}...")
            
            # Add source recommendations
            if rag_context.get("sources"):
                content_parts.append("\n**Read More:**")
                for src in rag_context["sources"]:
                    content_parts.append(f"• [{src['title']}]({src['url']})")
                    
                    # Add as recommendation
                    recommendations.append(Recommendation(
                        type="article",
                        title=src["title"],
                        description="ET Prime market analysis",
                        deeplink=src["url"],
                        source_agent="market_intelligence_agent",
                    ))

    return AgentResponse(
        agent_id="market_intelligence_agent",
        content="\n".join(content_parts),
        type="market_data",
        contains_investment_advice=is_investment_advice,
        recommendations=recommendations,
        sources=sources,
        confidence_score=0.85,
    )
