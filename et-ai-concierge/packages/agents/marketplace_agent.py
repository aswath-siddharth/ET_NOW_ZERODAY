"""
ET AI Concierge — Marketplace Agent (Agent 4)
Financial product intermediation: loans, insurance, credit cards, NPS, FDs.
"""
import math
from typing import Dict, Any, Optional, List
from state import AgentResponse, UserProfile, Recommendation
from config import settings


# ─── Privacy Filter ───────────────────────────────────────────────────────────

class PrivacyFilter:
    """Strip PII before any LLM call. Only minimum necessary data to the model."""
    ALLOWED_FIELDS_FOR_LLM = [
        "credit_score_band", "loan_amount", "tenure_months",
        "income_band", "employer_type", "age_group"
    ]

    def sanitize_for_llm(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in user_data.items() if k in self.ALLOWED_FIELDS_FOR_LLM}


privacy_filter = PrivacyFilter()


# ─── EMI Calculator ──────────────────────────────────────────────────────────

def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> Dict[str, Any]:
    """Calculate monthly EMI for a loan."""
    if annual_rate == 0:
        monthly_emi = principal / tenure_months
    else:
        monthly_rate = annual_rate / (12 * 100)
        monthly_emi = principal * monthly_rate * math.pow(1 + monthly_rate, tenure_months) / (
            math.pow(1 + monthly_rate, tenure_months) - 1
        )
    total_amount = monthly_emi * tenure_months
    total_interest = total_amount - principal

    return {
        "monthly_emi": round(monthly_emi, 2),
        "total_amount": round(total_amount, 2),
        "total_interest": round(total_interest, 2),
        "principal": principal,
        "rate": annual_rate,
        "tenure_months": tenure_months,
    }


# ─── Loan Rate Comparison ────────────────────────────────────────────────────

MOCK_LOAN_RATES = [
    {
        "bank": "SBI",
        "interest_rate": 8.40,
        "processing_fee": "0.35%",
        "max_tenure_years": 30,
        "approval_base_probability": 0.85,
    },
    {
        "bank": "HDFC",
        "interest_rate": 8.50,
        "processing_fee": "0.50%",
        "max_tenure_years": 30,
        "approval_base_probability": 0.80,
    },
    {
        "bank": "Kotak Mahindra",
        "interest_rate": 8.65,
        "processing_fee": "0.50%",
        "max_tenure_years": 25,
        "approval_base_probability": 0.75,
    },
    {
        "bank": "ICICI",
        "interest_rate": 8.55,
        "processing_fee": "0.50%",
        "max_tenure_years": 30,
        "approval_base_probability": 0.78,
    },
]


def _calculate_approval_probability(user: UserProfile, offer: Dict) -> float:
    """Estimate approval probability based on user profile."""
    base = offer["approval_base_probability"]
    # Adjust based on user attributes
    if user.income_type == "salaried":
        base += 0.05
    elif user.income_type == "business owner":
        base -= 0.05
    if user.age_group in ("20s", "30s"):
        base += 0.03
    return min(base, 0.99)


def compare_loan_rates(
    loan_amount: float,
    tenure_years: int,
    user: Optional[UserProfile] = None
) -> List[Dict[str, Any]]:
    """Compare loan rates across banks, ranked by approval probability."""
    tenure_months = tenure_years * 12
    results = []

    for offer in MOCK_LOAN_RATES:
        emi = calculate_emi(loan_amount, offer["interest_rate"], tenure_months)
        approval_prob = _calculate_approval_probability(user, offer) if user else offer["approval_base_probability"]

        results.append({
            "bank": offer["bank"],
            "interest_rate": offer["interest_rate"],
            "monthly_emi": emi["monthly_emi"],
            "total_interest": emi["total_interest"],
            "total_amount": emi["total_amount"],
            "processing_fee": offer["processing_fee"],
            "approval_probability": round(approval_prob * 100, 1),
        })

    # Sort by approval probability (desc), then by rate (asc)
    results.sort(key=lambda x: (-x["approval_probability"], x["interest_rate"]))
    return results


# ─── FD Rate Comparison ──────────────────────────────────────────────────────

MOCK_FD_RATES = [
    {"bank": "SBI", "1_year": 6.70, "3_year": 7.00, "5_year": 6.50},
    {"bank": "HDFC", "1_year": 6.60, "3_year": 7.10, "5_year": 7.00},
    {"bank": "ICICI", "1_year": 6.70, "3_year": 7.00, "5_year": 6.90},
    {"bank": "Kotak", "1_year": 6.20, "3_year": 6.50, "5_year": 6.50},
]


# ─── NPS Returns Calculator ──────────────────────────────────────────────────

def calculate_nps_returns(
    monthly_contribution: float,
    current_age: int,
    retirement_age: int = 60,
    expected_return: float = 10.0
) -> Dict[str, Any]:
    """Project NPS corpus at retirement."""
    years = retirement_age - current_age
    months = years * 12
    monthly_rate = expected_return / (12 * 100)

    if monthly_rate == 0:
        corpus = monthly_contribution * months
    else:
        corpus = monthly_contribution * (
            (math.pow(1 + monthly_rate, months) - 1) / monthly_rate
        ) * (1 + monthly_rate)

    # 60% annuity, 40% lump sum at retirement
    lump_sum = corpus * 0.4
    annuity_corpus = corpus * 0.6
    monthly_pension = annuity_corpus * 0.005  # ~6% annuity rate

    return {
        "total_corpus": round(corpus, 2),
        "lump_sum_at_retirement": round(lump_sum, 2),
        "estimated_monthly_pension": round(monthly_pension, 2),
        "total_invested": round(monthly_contribution * months, 2),
        "total_returns": round(corpus - (monthly_contribution * months), 2),
        "years_to_retirement": years,
    }


# ─── HITL Escalation ─────────────────────────────────────────────────────────

HITL_TRIGGERS = [
    lambda action_type, amount: action_type == "FUND_TRANSFER" and (amount or 0) > 100000,
    lambda action_type, amount: action_type == "INSURANCE_CLAIM",
    lambda action_type, amount: action_type == "LOAN_APPLICATION_SUBMIT",
]


def should_escalate(action_type: str, amount: float = 0) -> bool:
    return any(trigger(action_type, amount) for trigger in HITL_TRIGGERS)


# ─── Main Agent Function ─────────────────────────────────────────────────────

def run_marketplace_agent(user_message: str, profile: UserProfile) -> AgentResponse:
    """Process a message through the Marketplace Agent."""
    msg_lower = user_message.lower()
    content_parts = []
    recommendations = []
    is_investment_advice = False
    response_type = "marketplace"

    # ── Home Loan ──
    if any(word in msg_lower for word in ["home loan", "housing loan", "mortgage"]):
        amount = 5000000  # Default 50 lakh
        if "1 crore" in msg_lower or "1cr" in msg_lower:
            amount = 10000000
        elif "75 lakh" in msg_lower:
            amount = 7500000

        rates = compare_loan_rates(amount, 20, profile)
        top = rates[0]

        content_parts.append(f"🏠 **Home Loan Comparison (₹{amount/100000:.0f} Lakh, 20 years):**\n")
        content_parts.append("| Bank | Rate | EMI | Approval Chance |")
        content_parts.append("|------|------|-----|-----------------|")
        for r in rates:
            content_parts.append(
                f"| {r['bank']} | {r['interest_rate']}% | ₹{r['monthly_emi']:,.0f} | {r['approval_probability']}% |"
            )

        content_parts.append(
            f"\n💡 **Top Pick:** {top['bank']} — {top['approval_probability']}% approval "
            f"probability at {top['interest_rate']}% p.a."
        )
        is_investment_advice = True

        # Check HITL for loan application
        if "apply" in msg_lower or "submit" in msg_lower:
            response_type = "LOAN_APPLICATION"

    # ── EMI Calculator ──
    elif "emi" in msg_lower:
        emi = calculate_emi(5000000, 8.5, 240)
        content_parts.append("🧮 **EMI Calculation:**\n")
        content_parts.append(f"Loan Amount: ₹{emi['principal']:,.0f}")
        content_parts.append(f"Rate: {emi['rate']}% p.a.")
        content_parts.append(f"Tenure: {emi['tenure_months']} months")
        content_parts.append(f"**Monthly EMI: ₹{emi['monthly_emi']:,.0f}**")
        content_parts.append(f"Total Interest: ₹{emi['total_interest']:,.0f}")

    # ── FD Rates ──
    elif any(word in msg_lower for word in ["fd", "fixed deposit"]):
        content_parts.append("🏦 **Fixed Deposit Rates Comparison:**\n")
        content_parts.append("| Bank | 1 Year | 3 Year | 5 Year |")
        content_parts.append("|------|--------|--------|--------|")
        for fd in MOCK_FD_RATES:
            content_parts.append(f"| {fd['bank']} | {fd['1_year']}% | {fd['3_year']}% | {fd['5_year']}% |")

    # ── NPS ──
    elif "nps" in msg_lower or "pension" in msg_lower:
        age = 28 if profile.age_group in ("20s",) else 35
        nps = calculate_nps_returns(5000, age)
        content_parts.append("🏛️ **NPS Returns Projection:**\n")
        content_parts.append(f"Monthly Contribution: ₹5,000")
        content_parts.append(f"Years to Retirement: {nps['years_to_retirement']}")
        content_parts.append(f"**Projected Corpus: ₹{nps['total_corpus']:,.0f}**")
        content_parts.append(f"Lump Sum at 60: ₹{nps['lump_sum_at_retirement']:,.0f}")
        content_parts.append(f"Est. Monthly Pension: ₹{nps['estimated_monthly_pension']:,.0f}")
        is_investment_advice = True

    # ── Insurance ──
    elif any(word in msg_lower for word in ["insurance", "health cover"]):
        content_parts.append("🛡️ **Health Insurance Comparison:**\n")
        content_parts.append("| Plan | Cover | Premium/yr | Claim Ratio |")
        content_parts.append("|------|-------|------------|-------------|")
        content_parts.append("| Niva Bupa Health | ₹10L | ₹12,500 | 62% |")
        content_parts.append("| Star Health | ₹10L | ₹11,800 | 58% |")
        content_parts.append("| HDFC Ergo | ₹10L | ₹13,200 | 65% |")
        is_investment_advice = True

    # ── Credit Cards ──
    elif "credit card" in msg_lower:
        content_parts.append("💳 **Credit Card Comparison:**\n")
        content_parts.append("| Card | Annual Fee | Cashback | Lounge |")
        content_parts.append("|------|-----------|----------|--------|")
        content_parts.append("| ICICI Times Black | ₹5,000 | 2% | ✅ 8/yr |")
        content_parts.append("| SBI Cashback | ₹Nil | 5% Online | ❌ |")
        content_parts.append("| RuPay Select | ₹Nil | 1% | ✅ 4/yr |")

    # ── General ──
    else:
        content_parts.append(
            "🏪 **ET Marketplace** — I can help you with:\n"
            "• Home Loan comparison (SBI vs HDFC vs Kotak)\n"
            "• EMI calculations\n"
            "• Fixed Deposit rate comparison\n"
            "• NPS returns projection\n"
            "• Health Insurance comparison\n"
            "• Credit Card rewards analysis\n\n"
            "What would you like to explore?"
        )

    return AgentResponse(
        agent_id="marketplace_agent",
        content="\n".join(content_parts),
        type=response_type,
        contains_investment_advice=is_investment_advice,
        recommendations=recommendations,
        confidence_score=0.85,
    )
