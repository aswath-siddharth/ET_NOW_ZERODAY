import json

code = """
# ─── Mock Partner APIs (Phase 3) ─────────────────────────────────────────────

def fetch_mock_elss_funds():
    return [
        {"fund_name": "Quant Tax Plan", "returns_3yr": "24.5%", "risk": "High Risk", "rating": "5-Star"},
        {"fund_name": "SBI Long Term Equity", "returns_3yr": "22.1%", "risk": "High Risk", "rating": "5-Star"},
        {"fund_name": "Mirae Asset Tax Saver", "returns_3yr": "20.8%", "risk": "High Risk", "rating": "4-Star"}
    ]

def fetch_mock_insurance_quotes():
    return [
        {"provider": "HDFC Life", "cover": "1 Crore", "term": "30 Years", "monthly_premium": "₹1,200", "claim_settlement": "99.3%"},
        {"provider": "Max Life", "cover": "1 Crore", "term": "30 Years", "monthly_premium": "₹1,150", "claim_settlement": "99.5%"}
    ]
"""

with open("packages/agents/marketplace_agent.py", "a", encoding="utf-8") as f:
    f.write(code)
