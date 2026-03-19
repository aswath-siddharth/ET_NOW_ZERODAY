"""
ET AI Concierge — Seed Script: Ingest ET Prime Mock Articles
Run: python scripts/ingest_et_prime.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "rag", "ingestion"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "agents"))

from ingest import ingest_articles


MOCK_ARTICLES = [
    {
        "id": "art_001",
        "title": "Gold GIFT City Volumes Plunge 40% — What It Means for Investors",
        "sector": "Markets",
        "summary": "GIFT City's gold trading volumes have dropped significantly, signaling institutional repositioning.",
        "body": (
            "GIFT City's gold trading volumes have dropped 40% month-on-month, according to the latest "
            "exchange data. The decline, attributed to tighter RBI margin requirements and a global risk-off "
            "sentiment, could signal a pivotal moment for gold investors in India. Meanwhile, MCX gold futures "
            "continue to trade near all-time highs at ₹62,450 per 10 grams. Analysts at Motilal Oswal "
            "suggest that this divergence between GIFT City volumes and MCX prices indicates institutional "
            "players are shifting from exchange-traded gold to Sovereign Gold Bonds (SGBs), which offer "
            "2.5% annual interest plus capital appreciation. Retail investors with a 5-year horizon should "
            "consider SGBs over physical gold for tax-free returns."
        ),
        "url": "https://economictimes.indiatimes.com/markets/gold/gift-city-volumes",
        "tags": ["gold", "GIFT City", "institutional", "trading", "SGB"],
        "paywall": True
    },
    {
        "id": "art_002",
        "title": "Sovereign Gold Bonds vs Physical Gold: 2025 Returns Compared",
        "sector": "Personal Finance",
        "summary": "SGBs delivered 12.8% annualized returns vs 8.2% for physical gold.",
        "body": (
            "Sovereign Gold Bonds have outperformed physical gold by 4.6 percentage points over the past "
            "5 years, delivering 12.8% annualized returns compared to 8.2% for physical gold. The additional "
            "2.5% annual interest from SGBs, combined with zero capital gains tax on maturity, makes them "
            "the preferred gold investment vehicle for long-term investors. Physical gold carries making "
            "charges (8-25%), storage risks, and capital gains tax. The RBI has announced the next SGB "
            "tranche for April 2026. For investors looking to start a gold SIP, Paytm Money and Groww "
            "both offer digital gold accumulation plans starting at ₹100."
        ),
        "url": "https://economictimes.indiatimes.com/wealth/invest/sgb-vs-physical-gold",
        "tags": ["gold", "SGB", "sovereign gold bond", "returns", "comparison"],
        "paywall": False
    },
    {
        "id": "art_003",
        "title": "Nifty 50 Technical Analysis: Golden Cross Signals Bull Run",
        "sector": "Markets",
        "summary": "Nifty 50 has formed a Golden Cross pattern with 78% probability of 15%+ rally.",
        "body": (
            "The Nifty 50 index has formed a Golden Cross pattern — the 50-day simple moving average "
            "crossing above the 200-day SMA — for the first time since June 2023. Historical backtesting "
            "shows that this pattern has preceded a 15%+ rally within 6 months with 78% accuracy. "
            "Banking stocks (SBI, HDFC Bank, ICICI Bank) are leading the breakout, with the Bank Nifty "
            "outperforming the broader index by 3.2%. Traders should watch the 22,200 resistance level. "
            "A decisive close above it could trigger a move to 24,000. The RSI is at 62, indicating "
            "bullish momentum without overbought conditions."
        ),
        "url": "https://economictimes.indiatimes.com/markets/nifty-golden-cross",
        "tags": ["nifty", "technical analysis", "golden cross", "bull", "trading"],
        "paywall": True
    },
    {
        "id": "art_004",
        "title": "RBI Rate Cut: Home Loan EMIs to Drop by ₹1,200/month",
        "sector": "Real Estate",
        "summary": "25bps rate cut reduces SBI and HDFC home loan EMIs significantly.",
        "body": (
            "The RBI's Monetary Policy Committee (MPC) cut the repo rate by 25 basis points to 6.25%, "
            "the second cut in this easing cycle. For a ₹50 lakh home loan at SBI's new rate of 8.40% "
            "(down from 8.65%), the monthly EMI drops by approximately ₹1,200 over a 20-year tenure. "
            "HDFC Bank and Kotak Mahindra Bank have also announced rate reductions. Key highlights: "
            "SBI home loan rate: 8.40% (was 8.65%), HDFC: 8.50% (was 8.75%), Kotak: 8.65% (was 8.90%). "
            "First-time homebuyers in the ₹30L–₹75L segment benefit the most. The RBI governor hinted "
            "at another 25bps cut in the June 2026 review if inflation stays below 4.5%."
        ),
        "url": "https://economictimes.indiatimes.com/wealth/real-estate/rbi-rate-cut-emi",
        "tags": ["RBI", "rate cut", "home loan", "EMI", "SBI", "HDFC"],
        "paywall": False
    },
    {
        "id": "art_005",
        "title": "Best ELSS Funds 2025: Maximize Your Section 80C Savings",
        "sector": "Personal Finance",
        "summary": "Top 5 ELSS funds combining tax savings with wealth creation.",
        "body": (
            "With the financial year ending, here are the top 5 ELSS (Equity Linked Savings Schemes) "
            "funds for Section 80C tax deductions: 1. Axis Long Term Equity Fund: 18.5% 5Y CAGR, "
            "2. Mirae Asset Tax Saver: 17.2% 5Y CAGR, 3. SBI Long Term Equity: 16.8% 5Y CAGR, "
            "4. DSP Tax Saver: 15.9% 5Y CAGR, 5. Canara Robeco Equity Tax Saver: 16.1% 5Y CAGR. "
            "ELSS has the shortest lock-in period (3 years) among 80C instruments. For maximum tax "
            "benefit, invest up to ₹1.5 lakh per year. SIP mode is recommended over lump sum for "
            "rupee cost averaging. LTCG above ₹1 lakh is taxed at 10%."
        ),
        "url": "https://economictimes.indiatimes.com/wealth/tax/elss-funds-2025",
        "tags": ["ELSS", "80C", "tax saving", "mutual funds", "SIP"],
        "paywall": False
    },
    {
        "id": "art_006",
        "title": "Young Mind Entrepreneurs: 5 Startup Founders Under 25",
        "sector": "Startups",
        "summary": "Profiles of India's youngest startup founders and their funding journeys.",
        "body": (
            "India's startup ecosystem continues to produce remarkable young talent. Here are 5 founders "
            "under 25 who are making waves: 1. Priya Sharma (23) — FinLit, a financial literacy platform "
            "with 2M users, raised ₹15Cr Series A. 2. Arjun Patel (24) — AgriSync, connecting farmers "
            "directly to markets via WhatsApp, 500K+ transactions. 3. Zara Khan (22) — StyleAI, AI-powered "
            "personal styling, acquired by a major fashion retailer. These stories inspired the ET Young "
            "Mind Entrepreneurship Program, now in its 5th cohort. Applications open for the 6th cohort "
            "in April 2026. Past alumni have raised a combined ₹200Cr in funding."
        ),
        "url": "https://economictimes.indiatimes.com/startups/young-mind-founders",
        "tags": ["startups", "young mind", "entrepreneurs", "founders"],
        "paywall": True
    },
    {
        "id": "art_007",
        "title": "Portfolio Rebalancing: When to Shift from Equity to Debt",
        "sector": "Markets",
        "summary": "Expert guide on age-based and goal-based portfolio rebalancing strategies.",
        "body": (
            "Portfolio rebalancing is the secret weapon of disciplined investors. Here's a framework: "
            "Rule 1 — 100 minus your age in equity. A 30-year-old should have ~70% in equity, 30% in "
            "debt. Rule 2 — Rebalance when any asset class drifts more than 5% from target. Example: "
            "If your equity allocation grew to 80% due to a bull market, sell 10% of equity and move "
            "to debt funds. Rule 3 — Tax-efficient switching: Use balanced advantage funds which "
            "auto-rebalance without triggering capital gains. Top picks: ICICI Prudential Balanced "
            "Advantage (15.2% 5Y CAGR), HDFC Balanced Advantage (14.8% 5Y CAGR)."
        ),
        "url": "https://economictimes.indiatimes.com/markets/portfolio-rebalancing",
        "tags": ["portfolio", "rebalancing", "equity", "debt", "allocation"],
        "paywall": True
    },
    {
        "id": "art_008",
        "title": "NPS vs PPF: Which Retirement Plan Wins in 2025?",
        "sector": "Personal Finance",
        "summary": "NPS offers higher returns with market risk; PPF guarantees 7.1%.",
        "body": (
            "National Pension System (NPS) Tier I has delivered 11.2% average returns over 10 years "
            "in the equity scheme (Scheme E), while PPF guarantees 7.1% per annum. However, NPS requires "
            "60% to be invested in an annuity at retirement, which typically yields 5-6%. Tax benefits: "
            "NPS offers additional ₹50,000 deduction under 80CCD(1B) beyond the ₹1.5L 80C limit. "
            "PPF contributions are EEE (Exempt-Exempt-Exempt), making it entirely tax-free. "
            "Recommendation: Use both. PPF for guaranteed base, NPS for growth. Together, they offer "
            "up to ₹2L in annual tax deductions."
        ),
        "url": "https://economictimes.indiatimes.com/wealth/plan/nps-vs-ppf",
        "tags": ["NPS", "PPF", "retirement", "pension", "saving", "80C"],
        "paywall": False
    },
    {
        "id": "art_009",
        "title": "Auto Sector Rally: Tata Motors, M&M Lead the Charge",
        "sector": "Auto",
        "summary": "Auto stocks surge 25% YTD driven by EV demand and export growth.",
        "body": (
            "The auto sector has been the star performer of 2025-26, with the Nifty Auto index surging "
            "25% year-to-date. Tata Motors (+32%) leads the pack on strong JLR margins and EV sales "
            "growth. Mahindra & Mahindra (+28%) benefits from SUV market dominance and farm equipment "
            "recovery. Maruti Suzuki (+18%) is seeing revival in compact segment. EV penetration in "
            "passenger vehicles has crossed 5% for the first time. FAME III subsidies and state-level "
            "incentives are driving adoption. Analysts at Morgan Stanley have a 'Buy' rating on Tata "
            "Motors with a ₹1,100 target (current price: ₹870)."
        ),
        "url": "https://economictimes.indiatimes.com/markets/auto-rally",
        "tags": ["auto", "Tata Motors", "M&M", "EV", "stocks", "rally"],
        "paywall": True
    },
    {
        "id": "art_010",
        "title": "Health Insurance: Why ₹10 Lakh Cover Is Minimum in 2025",
        "sector": "Personal Finance",
        "summary": "Medical inflation at 14% demands higher health insurance coverage.",
        "body": (
            "With medical inflation running at 14% annually, a ₹5 lakh health insurance cover is "
            "no longer adequate. A single hospitalization for cardiac treatment can cost ₹8-12 lakh in "
            "metro cities. Here's our comparison: Niva Bupa Health Companion: ₹10L cover, ₹12,500/yr "
            "premium (30-year-old), claim settlement ratio 62%. Star Health Comprehensive: ₹10L cover, "
            "₹11,800/yr premium, claim settlement ratio 58%. HDFC Ergo Platinum: ₹10L cover, ₹13,200/yr "
            "premium, claim settlement ratio 65%. Key features to look for: restoration benefit, no room "
            "rent capping, daycare procedures coverage, and mental health coverage (now mandatory per IRDAI)."
        ),
        "url": "https://economictimes.indiatimes.com/wealth/insure/health-insurance-2025",
        "tags": ["insurance", "health", "Niva Bupa", "Star Health", "cover", "IRDAI"],
        "paywall": False
    },
]


if __name__ == "__main__":
    print("🚀 Seeding ET Prime mock articles into RAG pipeline...")
    ingest_articles(MOCK_ARTICLES)
    print("✅ Done! Articles are now searchable via Qdrant and Elasticsearch.")
