"""
Unit tests for Intent Router (intent_router.py).
Tests monetization intent triggers, tax vs insurance keywords,
and user profile state suppression.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from state import UserProfile
from intent_router import detect_upsell_intent


def test_detect_upsell_tax_trigger_active():
    profile = UserProfile(has_tax_investments=False)
    queries = [
        "How can I save tax under 80C?",
        "Tell me about ELSS mutual funds",
        "Best ways to get a tax deduction this year",
    ]
    for q in queries:
        res = detect_upsell_intent(q, profile)
        assert res["trigger_active"] is True
        assert res["trigger_type"] == "tax_marketplace"


def test_detect_upsell_tax_suppressed_when_already_invested():
    profile = UserProfile(has_tax_investments=True)
    res = detect_upsell_intent("How can I save tax under 80C?", profile)
    assert res["trigger_active"] is False


def test_detect_upsell_insurance_trigger_active():
    profile = UserProfile(has_insurance=False)
    queries = [
        "I need a health insurance policy for my family",
        "Should I buy a term plan?",
        "Looking for mediclaim coverage",
    ]
    for q in queries:
        res = detect_upsell_intent(q, profile)
        assert res["trigger_active"] is True
        assert res["trigger_type"] == "insurance_marketplace"


def test_detect_upsell_insurance_suppressed_when_already_covered():
    profile = UserProfile(has_insurance=True)
    res = detect_upsell_intent("Should I buy a term plan?", profile)
    assert res["trigger_active"] is False


def test_detect_upsell_no_trigger_for_general_queries():
    profile = UserProfile(has_tax_investments=False, has_insurance=False)
    queries = [
        "What is the Nifty 50 price?",
        "Tell me the latest tech news",
        "How do interest rates affect gold?",
    ]
    for q in queries:
        res = detect_upsell_intent(q, profile)
        assert res["trigger_active"] is False
        assert res["trigger_type"] is None
