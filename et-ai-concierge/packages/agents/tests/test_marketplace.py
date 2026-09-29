"""
Unit tests for Marketplace Agent (marketplace_agent.py).
Tests EMI calculations, zero-interest edge cases, approval probability logic,
privacy filter PII stripping, and financial product mocks.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from state import UserProfile, AgentResponse
from marketplace_agent import (
    calculate_emi, _calculate_approval_probability,
    privacy_filter, fetch_mock_elss_funds,
    fetch_mock_insurance_quotes, run_marketplace_agent,
)


def test_calculate_emi_standard():
    # 50 Lakhs at 8.5% for 20 years (240 months)
    res = calculate_emi(principal=5000000, annual_rate=8.5, tenure_months=240)
    assert res["principal"] == 5000000
    assert res["rate"] == 8.5
    assert res["tenure_months"] == 240
    assert 43000 < res["monthly_emi"] < 44000
    assert res["total_amount"] > res["principal"]
    assert res["total_interest"] == round(res["total_amount"] - res["principal"], 2)


def test_calculate_emi_zero_interest():
    # Zero interest: EMI must strictly be principal / tenure
    res = calculate_emi(principal=120000, annual_rate=0.0, tenure_months=12)
    assert res["monthly_emi"] == 10000.0
    assert res["total_interest"] == 0.0
    assert res["total_amount"] == 120000.0


def test_calculate_emi_short_tenure():
    res = calculate_emi(principal=100000, annual_rate=12.0, tenure_months=1)
    assert res["monthly_emi"] > 100000.0


def test_approval_probability_factors():
    offer = {"approval_base_probability": 0.50}

    # Best-case user: salaried, emergency fund, owning home, low risk
    good_user = UserProfile(
        income_type="salaried",
        has_emergency_fund=True,
        home_ownership="owning",
        risk_score=2,
    )
    prob_good = _calculate_approval_probability(good_user, offer)
    assert prob_good > 0.50

    # User with business income
    biz_user = UserProfile(
        income_type="business",
        has_emergency_fund=False,
        home_ownership="renting",
        risk_score=9,
    )
    prob_biz = _calculate_approval_probability(biz_user, offer)
    assert prob_biz < prob_good

    # Test clamping: should never exceed 1.0 or drop below 0.0
    high_base_offer = {"approval_base_probability": 0.95}
    clamped_high = _calculate_approval_probability(good_user, high_base_offer)
    assert clamped_high <= 1.0
    assert clamped_high >= 0.0


def test_privacy_filter_strips_pii():
    user_data = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+919876543210",
        "pan_card": "ABCDE1234F",
        "credit_score_band": "750+",
        "loan_amount": 5000000,
        "tenure_months": 240,
        "income_band": "15-25L",
        "employer_type": "MNC",
        "age_group": "30s",
    }
    sanitized = privacy_filter.sanitize_for_llm(user_data)

    assert "name" not in sanitized
    assert "email" not in sanitized
    assert "phone" not in sanitized
    assert "pan_card" not in sanitized
    assert sanitized["credit_score_band"] == "750+"
    assert sanitized["loan_amount"] == 5000000
    assert sanitized["tenure_months"] == 240


def test_fetch_mock_products():
    elss = fetch_mock_elss_funds()
    assert isinstance(elss, list)
    assert len(elss) > 0
    assert "fund_name" in elss[0]
    assert "returns_3yr" in elss[0]

    insurance = fetch_mock_insurance_quotes()
    assert isinstance(insurance, list)
    assert len(insurance) > 0
    assert "plan_name" in insurance[0] or "insurer" in insurance[0] or "provider" in insurance[0] or "coverage" in insurance[0]


def test_run_marketplace_agent():
    profile = UserProfile(persona="PERSONA_HOME_BUYER")
    response = run_marketplace_agent("I need a home loan of 50 lakhs", profile)
    assert isinstance(response, AgentResponse)
    assert response.agent_id == "marketplace_agent"
    assert len(response.content) > 0
